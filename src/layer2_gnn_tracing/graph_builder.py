"""Build the wallet→wallet directed graph used by GraphSAGE & pattern detectors."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import networkx as nx


@dataclass
class GraphBundle:
    """Light wrapper so we can shuttle data around without importing PyG everywhere."""
    node_ids: list[str]
    node_index: dict[str, int]
    node_features: np.ndarray            # (N, F)
    edge_index: np.ndarray               # (2, E)  src/dst indices
    edge_features: np.ndarray            # (E, Fe)
    labels: np.ndarray                   # (N,)   0/1, -1 = unlabeled
    nx_graph: nx.DiGraph


def _entity_to_node_features(ent_df: pd.DataFrame) -> np.ndarray:
    cols = [
        "age_days", "kyc_level",
        "txn_count_30d", "total_volume_30d", "avg_tx_amount",
        "distinct_counterparties_30d",
        "pep_flag", "sanction_flag", "has_crypto_activity",
    ]
    for c in cols:
        if c not in ent_df.columns:
            ent_df[c] = 0
    feats = ent_df[cols].astype(float).copy()
    # log-scale heavy-tailed columns
    feats["total_volume_30d"] = np.log1p(feats["total_volume_30d"].clip(lower=0))
    feats["avg_tx_amount"] = np.log1p(feats["avg_tx_amount"].clip(lower=0))
    return feats.values


def build_networkx_graph(edges_csv: Path, entities_csv: Path) -> GraphBundle:
    """Build a NetworkX DiGraph (used for pattern detection + viz)."""
    edges = pd.read_csv(edges_csv)
    ent = pd.read_csv(entities_csv)
    wallets = ent[ent.entity_type == "wallet"].copy().reset_index(drop=True)

    # Build node-index map covering wallets and any nodes that appear in edges
    all_node_ids = sorted(set(wallets.entity_id.tolist())
                          | set(edges["src"].tolist())
                          | set(edges["dst"].tolist()))
    node_index = {nid: i for i, nid in enumerate(all_node_ids)}

    # Align features (missing edge-only nodes get zeros)
    feats_df = wallets.set_index("entity_id")
    feats_df = feats_df.reindex(all_node_ids).fillna(0).reset_index().rename(columns={"index": "entity_id"})
    node_features = _entity_to_node_features(feats_df)

    # labels (default unknown = -1)
    label_col = wallets.set_index("entity_id").get("is_fraud", pd.Series(dtype=int))
    labels = np.full(len(all_node_ids), -1, dtype=int)
    for nid, lbl in label_col.items():
        if pd.notna(lbl):
            labels[node_index[nid]] = int(lbl)

    # edge index + features
    edge_index = np.vstack([
        edges["src"].map(node_index).values,
        edges["dst"].map(node_index).values,
    ])
    edge_features = edges[["weight", "tx_count"]].astype(float).values
    edge_features[:, 0] = np.log1p(edge_features[:, 0])  # log scale

    # nx graph (for patterns / viz)
    G = nx.DiGraph()
    G.add_nodes_from(all_node_ids)
    for _, r in edges.iterrows():
        G.add_edge(r["src"], r["dst"],
                   weight=float(r["weight"]),
                   tx_count=int(r["tx_count"]),
                   is_layering=int(r.get("is_layering", 0)))

    return GraphBundle(
        node_ids=all_node_ids,
        node_index=node_index,
        node_features=node_features.astype(np.float32),
        edge_index=edge_index.astype(np.int64),
        edge_features=edge_features.astype(np.float32),
        labels=labels,
        nx_graph=G,
    )


def build_pyg_graph(edges_csv: Path, entities_csv: Path):
    """Return a torch_geometric Data object alongside the GraphBundle."""
    try:
        import torch
        from torch_geometric.data import Data
    except ImportError as e:
        raise ImportError(
            "torch_geometric is required. Install with: pip install torch-geometric"
        ) from e

    bundle = build_networkx_graph(edges_csv, entities_csv)
    data = Data(
        x=torch.tensor(bundle.node_features, dtype=torch.float),
        edge_index=torch.tensor(bundle.edge_index, dtype=torch.long),
        edge_attr=torch.tensor(bundle.edge_features, dtype=torch.float),
        y=torch.tensor(np.clip(bundle.labels, 0, 1), dtype=torch.long),
    )
    # train mask: any labeled node
    data.train_mask = torch.tensor(bundle.labels >= 0, dtype=torch.bool)
    return data, bundle

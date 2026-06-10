"""Online crypto tracing: GNN fraud-score + layering pattern detection per seed wallet.

Two modes:
    - FULL:    GraphSAGE (PyTorch) + NetworkX layering — best, needs torch.
    - GRAPH:   NetworkX layering only + heuristic fraud scoring — works without torch.

The constructor auto-detects which mode to use based on availability.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from src.common.config import settings
from src.common.logger import get_logger
from src.common.schemas import GraphTraceResult, AlertType
from src.common.utils import model_path
from .graph_builder import build_networkx_graph, GraphBundle
from .patterns import detect_layering, extract_subgraph
from .train import MODEL_FILE

log = get_logger("layer2.trace")


def _heuristic_fraud_scores(bundle: GraphBundle) -> np.ndarray:
    """Cheap proxy when GNN isn't available.

    Score = mix of:
      - sanction_flag (strong signal)
      - layering involvement (incoming + outgoing edges in smurfing band)
      - PageRank centrality (proxy for layering hub)
    """
    import networkx as nx
    G = bundle.nx_graph
    n = len(bundle.node_ids)
    scores = np.zeros(n, dtype=np.float32)

    # 1. sanction_flag (column index 7 in node_features)
    sanction_col = 7
    if bundle.node_features.shape[1] > sanction_col:
        scores += bundle.node_features[:, sanction_col] * 0.5

    # 2. Layering-edge participation
    smurf_count = np.zeros(n, dtype=np.float32)
    for u, v, data in G.edges(data=True):
        w = float(data.get("weight", 0))
        if 40_000_000 <= w <= 49_999_999:
            iu = bundle.node_index.get(u)
            iv = bundle.node_index.get(v)
            if iu is not None:
                smurf_count[iu] += 1
            if iv is not None:
                smurf_count[iv] += 1
    smurf_norm = smurf_count / (smurf_count.max() + 1e-9)
    scores += smurf_norm * 0.35

    # 3. PageRank centrality
    try:
        pr = nx.pagerank(G, max_iter=50)
        pr_arr = np.array([pr.get(nid, 0.0) for nid in bundle.node_ids], dtype=np.float32)
        pr_norm = pr_arr / (pr_arr.max() + 1e-9)
        scores += pr_norm * 0.15
    except Exception:
        pass

    return np.clip(scores, 0, 1)


class CryptoTracer:
    """GNN + layering tracer. Falls back to heuristic when torch is missing."""

    def __init__(self, edges_csv: Optional[Path] = None,
                 entities_csv: Optional[Path] = None,
                 model_version: str = "0.1.0"):
        edges_csv = edges_csv or settings.app_data_dir / "sample" / "crypto_edges.csv"
        entities_csv = entities_csv or settings.app_data_dir / "sample" / "entities.csv"

        # Always build the NetworkX graph (no torch needed)
        bundle = build_networkx_graph(edges_csv, entities_csv)

        self.bundle: GraphBundle = bundle
        self.model_version = model_version
        self.mode: str = "graph-only"
        self.fraud_scores: np.ndarray

        # Try to load the GNN — if torch isn't available or weights missing, fall back
        try:
            import torch
            from .graphsage_model import GraphSAGE
            from .graph_builder import build_pyg_graph
            path = model_path(MODEL_FILE)
            if not path.exists():
                raise FileNotFoundError(f"GNN weights missing at {path}")
            data, _ = build_pyg_graph(edges_csv, entities_csv)
            blob = torch.load(path, map_location="cpu", weights_only=False)
            model = GraphSAGE(blob["in_dim"], hidden_dim=blob["hidden_dim"])
            model.load_state_dict(blob["state_dict"])
            model.eval()
            with torch.no_grad():
                self.fraud_scores = model.fraud_proba(data.x, data.edge_index).cpu().numpy()
            self.mode = "gnn"
            log.info("layer2.tracer.gnn_loaded")
        except Exception as e:
            log.warning("layer2.tracer.heuristic_fallback", error=str(e))
            self.fraud_scores = _heuristic_fraud_scores(bundle)
            self.mode = "graph-only"

    def fraud_score(self, wallet: str) -> float:
        i = self.bundle.node_index.get(wallet)
        if i is None:
            return 0.0
        return float(self.fraud_scores[i])

    def trace(self, seed_wallet: str, *, hops: int = 2) -> GraphTraceResult:
        if seed_wallet not in self.bundle.node_index:
            return GraphTraceResult(
                seed_wallet=seed_wallet, subgraph_size=0,
                layering_score=0.0, flagged_wallets=[], path_count=0,
                max_hop=0, pattern_types=[], explanation="Wallet not found in graph",
            )
        sub = extract_subgraph(self.bundle.nx_graph, seed_wallet, hops=hops)
        evidence = detect_layering(self.bundle.nx_graph, seed_wallet)

        # Flag wallets in the subgraph whose GNN score exceeds the threshold
        flagged: list[str] = []
        for w in sub.nodes:
            idx = self.bundle.node_index.get(w)
            if idx is None:
                continue
            if self.fraud_scores[idx] >= settings.gnn_layering_threshold:
                flagged.append(w)

        patterns: list[AlertType] = []
        if evidence.smurfing_edges > 0:
            patterns.append(AlertType.SMURFING)
        if len(evidence.chains) > 0:
            patterns.append(AlertType.LAYERING)
        if not patterns and flagged:
            patterns.append(AlertType.ANOMALOUS_PATTERN)

        explanation = (
            f"Subgraph {sub.number_of_nodes()} nodes / {sub.number_of_edges()} edges. "
            f"GNN flagged {len(flagged)} wallets. "
            f"Detected {len(evidence.chains)} layering chains across "
            f"{evidence.smurfing_edges} smurfing hops "
            f"(IDR {evidence.suspicious_value:,.0f} suspicious value)."
        )

        return GraphTraceResult(
            seed_wallet=seed_wallet,
            subgraph_size=sub.number_of_nodes(),
            layering_score=evidence.layering_score,
            flagged_wallets=flagged,
            path_count=len(evidence.chains),
            max_hop=hops,
            pattern_types=patterns,
            explanation=explanation,
        )

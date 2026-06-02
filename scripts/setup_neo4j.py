"""Bootstrap Neo4j with the wallet graph for Layer 2 production use."""
from __future__ import annotations

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
from pathlib import Path

import pandas as pd

from src.common.config import settings
from src.common.logger import get_logger
from src.layer2_gnn_tracing.neo4j_client import Neo4jClient

log = get_logger("setup.neo4j")


def main(edges_csv: Path, entities_csv: Path) -> None:
    client = Neo4jClient()
    client.setup_constraints()

    ent = pd.read_csv(entities_csv)
    wallets = ent[ent.entity_type == "wallet"]
    log.info("setup.upsert_wallets", n=len(wallets))
    wallets_payload = [
        {"id": w.entity_id, "chain": "eth",
         "fraud_score": 0.0,
         "is_known_bad": bool(w.is_fraud)}
        for _, w in wallets.iterrows()
    ]
    client.upsert_wallets(wallets_payload)

    edges = pd.read_csv(edges_csv)
    log.info("setup.upsert_edges", n=len(edges))
    edges_payload = [
        {"src": r["src"], "dst": r["dst"],
         "weight": float(r["weight"]),
         "tx_count": int(r["tx_count"])}
        for _, r in edges.iterrows()
    ]
    # batch to avoid Cypher timeout
    BATCH = 5000
    for i in range(0, len(edges_payload), BATCH):
        client.upsert_edges(edges_payload[i:i + BATCH])

    log.info("setup.done")
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edges", type=Path,
                        default=settings.app_data_dir / "sample" / "crypto_edges.csv")
    parser.add_argument("--entities", type=Path,
                        default=settings.app_data_dir / "sample" / "entities.csv")
    args = parser.parse_args()
    main(args.edges, args.entities)

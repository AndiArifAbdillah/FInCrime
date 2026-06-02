"""Train all four FinCrime model layers in sequence."""
from __future__ import annotations

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import time
from pathlib import Path

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("train_all")


def main(data_dir: Path, model_dir: Path) -> None:
    sample = data_dir / "sample"
    entities = sample / "entities.csv"
    transactions = sample / "transactions.csv"
    edges = sample / "crypto_edges.csv"

    for p in (entities, transactions, edges):
        if not p.exists():
            raise FileNotFoundError(
                f"Missing {p}. Run `python scripts/generate_sample_data.py` first.")

    # ----- Layer 0 -----
    log.info("=" * 60)
    log.info("Layer 0 — Risk Scoring (XGBoost + SHAP)")
    log.info("=" * 60)
    t0 = time.time()
    from src.layer0_risk_scoring.train import train as train_l0
    m0 = train_l0(entities, model_dir)
    log.info("layer0.done", elapsed=f"{time.time()-t0:.1f}s",
             roc_auc=m0["metrics"]["roc_auc"])

    # ----- Layer 1 -----
    log.info("=" * 60)
    log.info("Layer 1 — Fraud Detection (Isolation Forest + Autoencoder)")
    log.info("=" * 60)
    t0 = time.time()
    from src.layer1_fraud_detection.train import train as train_l1
    m1 = train_l1(transactions, model_dir, ae_epochs=15)
    log.info("layer1.done", elapsed=f"{time.time()-t0:.1f}s")

    # ----- Layer 2 -----
    log.info("=" * 60)
    log.info("Layer 2 — GraphSAGE Crypto Tracing")
    log.info("=" * 60)
    t0 = time.time()
    try:
        from src.layer2_gnn_tracing.train import train as train_l2
        m2 = train_l2(edges, entities, model_dir, epochs=50)
        log.info("layer2.done", elapsed=f"{time.time()-t0:.1f}s",
                 best_val_auc=m2["best_val_auc"])
    except ImportError as e:
        log.warning("layer2.skipped (torch_geometric not installed)", error=str(e))

    log.info("=" * 60)
    log.info("All trainable layers complete. Models in: %s", model_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=settings.app_data_dir)
    parser.add_argument("--model-dir", type=Path, default=settings.app_models_dir)
    args = parser.parse_args()
    main(args.data_dir, args.model_dir)

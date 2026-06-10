"""Re-train all layers with MLflow tracking enabled.

Usage:
    .\fc python scripts/train_with_mlflow.py

View runs:
    .\fc python -m mlflow ui --backend-store-uri file:./data/mlruns
    # then open http://localhost:5000
"""
from __future__ import annotations

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import joblib

from src.common.config import settings
from src.common.logger import get_logger
from src.mlops import MLflowTracker

log = get_logger("train_with_mlflow")


def train_layer0_mlflow():
    from src.layer0_risk_scoring.train import train
    with MLflowTracker(experiment="fincrime_layer0_risk_scoring",
                       tags={"layer": "0", "model_type": "xgboost"}) as t:
        meta = train(
            settings.app_data_dir / "sample" / "entities.csv",
            settings.app_models_dir,
        )
        t.log_params({"model_type": "xgboost", "task": "binary_classification"})
        t.log_metrics(meta.get("metrics", {}))
        for fname in ("layer0_risk_scoring.joblib", "layer0_risk_scoring.meta.json"):
            p = settings.app_models_dir / fname
            if p.exists():
                t.log_artifact(p)
        # log the actual sklearn-compatible booster
        bundle = joblib.load(settings.app_models_dir / "layer0_risk_scoring.joblib")
        t.log_sklearn_model(bundle["model"])
        return meta


def train_layer1_mlflow():
    from src.layer1_fraud_detection.train import train
    with MLflowTracker(experiment="fincrime_layer1_fraud_detection",
                       tags={"layer": "1", "model_type": "iforest+ae"}) as t:
        meta = train(
            settings.app_data_dir / "sample" / "transactions.csv",
            settings.app_models_dir, ae_epochs=15,
        )
        t.log_params({
            "model_type": "isolation_forest+autoencoder",
            "contamination": meta.get("contamination"),
            "ae_enabled": meta.get("ae_enabled"),
        })
        t.log_metrics({
            "ae_threshold": meta.get("ae_threshold") or 0,
            "n_train": meta.get("n_train", 0),
        })
        for fname in ("layer1_isolation_forest.joblib", "layer1_scaler.joblib",
                      "layer1_fraud_detection.meta.json"):
            p = settings.app_models_dir / fname
            if p.exists():
                t.log_artifact(p)
        return meta


def train_layer2_mlflow():
    try:
        from src.layer2_gnn_tracing.train import train
        edges = settings.app_data_dir / "sample" / "crypto_edges.csv"
        ent = settings.app_data_dir / "sample" / "entities.csv"
        with MLflowTracker(experiment="fincrime_layer2_graphsage",
                           tags={"layer": "2", "model_type": "graphsage"}) as t:
            meta = train(edges, ent, settings.app_models_dir, epochs=50)
            t.log_params({"model_type": "graphsage", "hidden_dim": meta.get("hidden_dim"),
                          "epochs": meta.get("epochs"), "in_dim": meta.get("in_dim")})
            t.log_metrics({"best_val_auc": meta.get("best_val_auc", 0)})
            for fname in ("layer2_graphsage.pt", "layer2_graphsage.meta.json"):
                p = settings.app_models_dir / fname
                if p.exists():
                    t.log_artifact(p)
            return meta
    except ImportError as e:
        log.warning("layer2 skipped — no torch_geometric", error=str(e))
        return None


def main():
    print("\n" + "=" * 70)
    print("  TRAINING ALL LAYERS WITH MLFLOW TRACKING")
    print("=" * 70)

    meta0 = train_layer0_mlflow()
    print(f"\n[Layer 0] ROC AUC: {meta0['metrics']['roc_auc']:.4f}")

    meta1 = train_layer1_mlflow()
    print(f"[Layer 1] Done, AE enabled: {meta1.get('ae_enabled')}")

    meta2 = train_layer2_mlflow()
    if meta2:
        print(f"[Layer 2] Best val AUC: {meta2.get('best_val_auc', 0):.4f}")

    print("\n" + "=" * 70)
    print("  All runs logged to MLflow")
    print("=" * 70)
    print("  View at:  http://localhost:5000  (run: mlflow ui)")
    print("  Or:       .\\fc python -m mlflow ui --backend-store-uri file:./data/mlruns")


if __name__ == "__main__":
    main()

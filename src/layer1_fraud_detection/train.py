"""Train Layer 1 Isolation Forest (+ optional Autoencoder if torch is available)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.common.config import settings
from src.common.logger import get_logger
from src.common.utils import ensure_model_dir
from .autoencoder import fit_autoencoder, save_autoencoder, torch_available
from .features import tx_features, ALL_TX_FEATURES

log = get_logger("layer1.train")

IF_FILE = "layer1_isolation_forest.joblib"
AE_FILE = "layer1_autoencoder.pt"
SCALER_FILE = "layer1_scaler.joblib"
META_FILE = "layer1_fraud_detection.meta.json"


def train(transactions_csv: Path, model_dir: Path | None = None,
          contamination: float = 0.05, ae_epochs: int = 15,
          use_autoencoder: bool | None = None) -> dict:
    model_dir = model_dir or ensure_model_dir()
    log.info("layer1.train.start", csv=str(transactions_csv))
    df = pd.read_csv(transactions_csv)

    X = tx_features(df).values
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    # IsolationForest
    iso = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    ).fit(Xs)
    joblib.dump(iso, model_dir / IF_FILE)
    joblib.dump(scaler, model_dir / SCALER_FILE)

    # Autoencoder (optional)
    if use_autoencoder is None:
        use_autoencoder = torch_available()
    ae_threshold = None
    if use_autoencoder:
        ae, ae_threshold = fit_autoencoder(Xs.astype(np.float32), epochs=ae_epochs)
        save_autoencoder(ae, model_dir / AE_FILE, ae_threshold, Xs.shape[1])
        log.info("layer1.autoencoder.trained", threshold=ae_threshold)
    else:
        log.warning("layer1.autoencoder.skipped",
                    reason="torch unavailable" if not torch_available() else "disabled")

    meta = {
        "features": ALL_TX_FEATURES,
        "contamination": contamination,
        "ae_threshold": ae_threshold,
        "ae_enabled": bool(use_autoencoder),
        "n_train": int(len(df)),
        "model_version": "0.1.0",
    }
    (model_dir / META_FILE).write_text(json.dumps(meta, indent=2))
    log.info("layer1.train.done", **{k: v for k, v in meta.items() if k != "features"})
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", type=Path,
                        default=settings.app_data_dir / "sample" / "transactions.csv")
    parser.add_argument("--model-dir", type=Path, default=settings.app_models_dir)
    parser.add_argument("--contamination", type=float, default=0.05)
    parser.add_argument("--ae-epochs", type=int, default=15)
    parser.add_argument("--no-ae", action="store_true",
                        help="Skip autoencoder even if torch is installed")
    args = parser.parse_args()
    train(args.transactions, args.model_dir, args.contamination, args.ae_epochs,
          use_autoencoder=False if args.no_ae else None)

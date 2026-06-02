"""Train the XGBoost risk-scoring model and persist it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
import xgboost as xgb

from src.common.config import settings
from src.common.logger import get_logger
from src.common.utils import ensure_model_dir
from .features import build_features, ALL_FEATURES

log = get_logger("layer0.train")

MODEL_FILE = "layer0_risk_scoring.joblib"
META_FILE = "layer0_risk_scoring.meta.json"


def train(entities_csv: Path, model_dir: Path | None = None) -> dict:
    model_dir = model_dir or ensure_model_dir()
    log.info("layer0.train.start", entities_csv=str(entities_csv))
    df = pd.read_csv(entities_csv)
    if "is_fraud" not in df.columns:
        raise ValueError("entities.csv must contain a `is_fraud` label column")

    X = build_features(df)
    y = df["is_fraud"].astype(int).values

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pos = int(y_tr.sum())
    neg = int(len(y_tr) - pos)
    scale = max(1.0, neg / max(pos, 1))

    model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="binary:logistic",
        eval_metric="aucpr",
        scale_pos_weight=scale,
        random_state=42,
        tree_method="hist",
        n_jobs=-1,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(y_te, proba)),
        "pr_auc": float(average_precision_score(y_te, proba)),
        "precision": float(precision_score(y_te, pred, zero_division=0)),
        "recall": float(recall_score(y_te, pred, zero_division=0)),
        "f1": float(f1_score(y_te, pred, zero_division=0)),
        "n_train": int(len(y_tr)),
        "n_test": int(len(y_te)),
        "positive_rate": float(y.mean()),
    }
    log.info("layer0.train.metrics", **metrics)

    model_path = model_dir / MODEL_FILE
    joblib.dump({"model": model, "features": ALL_FEATURES}, model_path)
    log.info("layer0.train.saved", path=str(model_path))

    meta = {"metrics": metrics, "features": ALL_FEATURES, "model_version": "0.1.0"}
    (model_dir / META_FILE).write_text(json.dumps(meta, indent=2))
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--entities", type=Path,
                        default=settings.app_data_dir / "sample" / "entities.csv")
    parser.add_argument("--model-dir", type=Path, default=settings.app_models_dir)
    args = parser.parse_args()
    train(args.entities, args.model_dir)

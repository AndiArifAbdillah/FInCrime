"""Model monitoring endpoints — drift detection + layer health."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.common.config import settings
from src.monitoring import (
    compute_feature_drift_report, compute_layer_health, PredictionLogger,
)

router = APIRouter()


@router.get("/v1/monitoring/health")
def all_layer_health():
    """Aggregate stats per layer over last 24h."""
    return {
        "windows_hours": 24,
        "layers": [
            compute_layer_health("layer0").__dict__,
            compute_layer_health("layer1").__dict__,
            compute_layer_health("layer2").__dict__,
        ],
    }


@router.get("/v1/monitoring/drift")
def feature_drift(
    baseline: str = Query("data/sample/entities.csv"),
    current: str = Query("data/sample/entities.csv"),
    feature_set: str = Query("entities"),
):
    """Compute drift between baseline & current CSV files."""
    b_path = Path(baseline)
    c_path = Path(current)
    if not b_path.exists() or not c_path.exists():
        raise HTTPException(404, f"File not found: {baseline} / {current}")
    b_df = pd.read_csv(b_path)
    c_df = pd.read_csv(c_path)
    # For demo: split data in half to simulate baseline-vs-current
    if baseline == current:
        n = len(b_df)
        b_df = b_df.iloc[: n // 2]
        c_df = c_df.iloc[n // 2 :]
    rep = compute_feature_drift_report(b_df, c_df)
    return {
        "overall_psi": rep.overall_psi,
        "overall_severity": rep.overall_severity,
        "n_baseline": rep.n_baseline,
        "n_current": rep.n_current,
        "feature_drifts": [d.__dict__ for d in rep.feature_drifts[:15]],
    }


@router.post("/v1/monitoring/seed-demo")
def seed_demo_predictions(n: int = 200):
    """Generate fake prediction history for demo (so health endpoint isn't empty)."""
    import random
    logger = PredictionLogger()
    for i in range(n):
        layer = random.choice(["layer0", "layer1", "layer2"])
        score = random.random()
        logger.log(
            layer=layer, subject=f"demo_{i}",
            score=score, is_alert=score >= 0.7,
        )
    return {"ok": True, "n": n}

"""Prediction logging + layer health summaries."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from src.common.utils import utc_now
from pathlib import Path
from typing import Optional

from src.common.config import settings
from src.common.logger import get_logger
from src.common.utils import now_iso

log = get_logger("monitoring.metrics")

DEFAULT_DB = settings.app_data_dir / "fincrime_metrics.db"


@dataclass
class LayerHealth:
    layer: str
    total_predictions: int
    alert_rate: float          # fraction of predictions flagged
    avg_score: float
    p95_score: float
    last_prediction_at: str


class PredictionLogger:
    """SQLite-backed prediction log (very simple, append-only)."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    layer       TEXT NOT NULL,
                    subject     TEXT,
                    score       REAL,
                    is_alert    INTEGER,
                    model_ver   TEXT,
                    ts          TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_pred_layer_ts ON predictions(layer, ts);
            """)

    def log(self, *, layer: str, subject: str, score: float,
            is_alert: bool, model_ver: str = "0.1.0"):
        with self._conn() as c:
            c.execute(
                "INSERT INTO predictions (layer, subject, score, is_alert, model_ver, ts) "
                "VALUES (?,?,?,?,?,?)",
                (layer, subject, float(score), 1 if is_alert else 0, model_ver, now_iso()),
            )


def compute_layer_health(layer: str, db_path: Optional[Path] = None,
                         window_hours: int = 24) -> Optional[LayerHealth]:
    """Aggregate prediction stats over the last `window_hours` for a layer."""
    db_path = db_path or DEFAULT_DB
    if not db_path.exists():
        return LayerHealth(layer=layer, total_predictions=0,
                           alert_rate=0.0, avg_score=0.0, p95_score=0.0,
                           last_prediction_at="")
    cutoff = (utc_now() - timedelta(hours=window_hours)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT score, is_alert, ts FROM predictions WHERE layer=? AND ts>=?",
            (layer, cutoff),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return LayerHealth(layer=layer, total_predictions=0,
                           alert_rate=0.0, avg_score=0.0, p95_score=0.0,
                           last_prediction_at="")
    scores = [r[0] for r in rows]
    alerts = sum(r[1] for r in rows)
    import numpy as np
    return LayerHealth(
        layer=layer,
        total_predictions=len(rows),
        alert_rate=round(alerts / max(len(rows), 1), 4),
        avg_score=round(float(np.mean(scores)), 4),
        p95_score=round(float(np.quantile(scores, 0.95)), 4),
        last_prediction_at=max(r[2] for r in rows),
    )

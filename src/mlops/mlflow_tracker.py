"""MLflow integration wrapper.

Setup:
    1. pip install mlflow
    2. Set MLFLOW_TRACKING_URI in .env (e.g., 'file:./mlruns' or 'http://mlflow:5000')
    3. Run: mlflow ui  (opens http://localhost:5000)

This module degrades gracefully when mlflow isn't installed — training still
works, it just doesn't log to MLflow.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("mlops.mlflow")

try:
    import mlflow
    import mlflow.sklearn
    import mlflow.pytorch
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


class MLflowTracker:
    """Wraps mlflow.start_run + log_param/log_metric/log_artifact + register model.

    Designed so that every layer's `train()` can call the same 3 methods:
        with MLflowTracker(experiment="layer0_risk_scoring") as t:
            t.log_params({...})
            t.log_metrics({...})
            t.log_model(model, "model.pkl")
    """

    def __init__(self, experiment: str = "fincrime_default",
                 tracking_uri: Optional[str] = None,
                 run_name: Optional[str] = None,
                 tags: Optional[dict] = None):
        self.experiment = experiment
        self.tracking_uri = tracking_uri or os.environ.get(
            "MLFLOW_TRACKING_URI", f"file:{settings.app_data_dir / 'mlruns'}"
        )
        self.run_name = run_name
        self.tags = tags or {}
        self._run = None

    def __enter__(self):
        if not _AVAILABLE:
            log.warning("mlflow.unavailable — no-op tracker")
            return self
        try:
            mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment(self.experiment)
            self._run = mlflow.start_run(run_name=self.run_name)
            if self.tags:
                mlflow.set_tags(self.tags)
            log.info("mlflow.run_started",
                     experiment=self.experiment,
                     run_id=self._run.info.run_id)
        except Exception as e:
            log.warning("mlflow.start_failed", error=str(e))
            self._run = None
        return self

    def __exit__(self, exc_type, exc, tb):
        if _AVAILABLE and self._run:
            try:
                if exc:
                    mlflow.set_tag("status", "failed")
                    mlflow.set_tag("error", str(exc)[:200])
                mlflow.end_run()
                log.info("mlflow.run_ended", run_id=self._run.info.run_id)
            except Exception as e:
                log.warning("mlflow.end_failed", error=str(e))

    def log_params(self, params: dict[str, Any]) -> None:
        if _AVAILABLE and self._run:
            try:
                mlflow.log_params(params)
            except Exception as e:
                log.warning("mlflow.log_params_failed", error=str(e))

    def log_metrics(self, metrics: dict[str, float]) -> None:
        if _AVAILABLE and self._run:
            try:
                mlflow.log_metrics({k: float(v) for k, v in metrics.items()
                                    if isinstance(v, (int, float))})
            except Exception as e:
                log.warning("mlflow.log_metrics_failed", error=str(e))

    def log_artifact(self, local_path: Path) -> None:
        if _AVAILABLE and self._run:
            try:
                mlflow.log_artifact(str(local_path))
            except Exception as e:
                log.warning("mlflow.log_artifact_failed", error=str(e))

    def log_sklearn_model(self, model, artifact_path: str = "model") -> None:
        if _AVAILABLE and self._run:
            try:
                mlflow.sklearn.log_model(model, artifact_path)
            except Exception as e:
                log.warning("mlflow.log_sklearn_failed", error=str(e))

    def log_pytorch_model(self, model, artifact_path: str = "model") -> None:
        if _AVAILABLE and self._run:
            try:
                mlflow.pytorch.log_model(model, artifact_path)
            except Exception as e:
                log.warning("mlflow.log_pytorch_failed", error=str(e))


@contextmanager
def mlflow_track(experiment: str, **kwargs):
    """Shorter context-manager form."""
    with MLflowTracker(experiment=experiment, **kwargs) as t:
        yield t

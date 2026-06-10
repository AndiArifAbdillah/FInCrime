"""Online risk-scoring + SHAP explainability for Layer 0."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from src.common.logger import get_logger
from src.common.schemas import Entity, RiskScore
from src.common.utils import model_path, now_dt, risk_level_from_score
from .features import build_features
from .train import MODEL_FILE

log = get_logger("layer0.predict")


class RiskScorer:
    """Loads the trained XGBoost bundle and serves real-time scores with SHAP top-factor explanations."""

    def __init__(self, model_file: Path | None = None, model_version: str = "0.1.0"):
        path = model_file or model_path(MODEL_FILE)
        if not path.exists():
            raise FileNotFoundError(
                f"Risk-scoring model not found at {path}. "
                "Run: python -m src.layer0_risk_scoring.train"
            )
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.features = bundle["features"]
        self.model_version = model_version
        self._explainer = None  # lazy

    # ------- explainer (lazy because SHAP imports are heavy) -------
    def _shap(self):
        if self._explainer is None:
            try:
                import shap
            except ImportError:
                log.warning("shap not installed — SHAP explanations disabled")
                return None
            self._explainer = shap.TreeExplainer(self.model)
        return self._explainer

    # ------- scoring -------
    def score_one(self, entity: Entity, with_shap: bool = True) -> RiskScore:
        df = pd.DataFrame([entity.model_dump()])
        X = build_features(df)
        proba = float(self.model.predict_proba(X)[0, 1])
        score = round(proba * 100, 2)
        top_factors: list[dict] = []
        if with_shap:
            explainer = self._shap()
            if explainer is not None:
                shap_vals = explainer.shap_values(X)
                row = shap_vals[0]
                order = np.argsort(np.abs(row))[::-1][:5]
                top_factors = [
                    {"feature": self.features[i],
                     "value": float(X.iloc[0, i]),
                     "contribution": float(row[i])}
                    for i in order
                ]
            else:
                # Fallback: use XGBoost's built-in feature_importances_
                imp = self.model.feature_importances_
                order = np.argsort(imp)[::-1][:5]
                top_factors = [
                    {"feature": self.features[i],
                     "value": float(X.iloc[0, i]),
                     "contribution": float(imp[i])}
                    for i in order
                ]
        return RiskScore(
            entity_id=entity.entity_id,
            score=score,
            level=risk_level_from_score(score),
            top_factors=top_factors,
            model_version=self.model_version,
            computed_at=now_dt(),
        )

    def score_batch(self, entities: Iterable[Entity]) -> list[RiskScore]:
        ent_list = list(entities)
        if not ent_list:
            return []
        df = pd.DataFrame([e.model_dump() for e in ent_list])
        X = build_features(df)
        proba = self.model.predict_proba(X)[:, 1]
        scores = (proba * 100).round(2)
        out: list[RiskScore] = []
        for ent, s in zip(ent_list, scores):
            out.append(
                RiskScore(
                    entity_id=ent.entity_id,
                    score=float(s),
                    level=risk_level_from_score(float(s)),
                    top_factors=[],
                    model_version=self.model_version,
                    computed_at=now_dt(),
                )
            )
        return out

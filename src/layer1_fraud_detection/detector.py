"""Real-time fraud detection orchestrator: Isolation Forest + (optional) Autoencoder + rules."""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from src.common.config import settings
from src.common.logger import get_logger
from src.common.schemas import Transaction, FraudPrediction, AlertType
from src.common.utils import model_path, now_dt
from .autoencoder import load_autoencoder, reconstruction_error, torch_available
from .features import tx_features
from .rules import apply_rules
from .train import IF_FILE, AE_FILE, SCALER_FILE, META_FILE

log = get_logger("layer1.detect")


class FraudDetector:
    def __init__(self, model_version: str = "0.1.0"):
        if_path = model_path(IF_FILE)
        sc_path = model_path(SCALER_FILE)
        for p in (if_path, sc_path):
            if not p.exists():
                raise FileNotFoundError(
                    f"Layer 1 artifact missing: {p}. Train first via "
                    "`python -m src.layer1_fraud_detection.train`"
                )
        self.iforest = joblib.load(if_path)
        self.scaler = joblib.load(sc_path)
        self.model_version = model_version

        # Load autoencoder if both torch is available AND we trained one
        self.ae = None
        self.ae_threshold = None
        meta_path = model_path(META_FILE)
        ae_enabled = False
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                ae_enabled = bool(meta.get("ae_enabled", False))
            except Exception:
                pass
        ae_path = model_path(AE_FILE)
        if ae_enabled and torch_available() and ae_path.exists():
            try:
                self.ae, self.ae_threshold = load_autoencoder(ae_path)
                log.info("layer1.autoencoder.loaded")
            except Exception as e:
                log.warning("layer1.autoencoder.load_failed", error=str(e))

    def _score_raw(self, df: pd.DataFrame) -> np.ndarray:
        X = tx_features(df).values
        Xs = self.scaler.transform(X)

        if_score = -self.iforest.decision_function(Xs)
        if len(if_score) > 1:
            rng = float(np.ptp(if_score))
            if_p = (if_score - if_score.min()) / (rng + 1e-9) if rng > 0 else np.zeros_like(if_score)
        else:
            if_p = np.clip(if_score, 0, 1)

        if self.ae is not None and self.ae_threshold is not None:
            recon = reconstruction_error(self.ae, Xs.astype(np.float32))
            ae_p = np.clip(recon / (self.ae_threshold + 1e-9) / 2.0, 0, 1)
            return 0.5 * if_p + 0.5 * ae_p
        return if_p

    def predict_one(self, tx: Transaction) -> FraudPrediction:
        df = pd.DataFrame([tx.model_dump()])
        score = float(self._score_raw(df)[0])
        rule_alerts = apply_rules(tx.model_dump())
        is_anomaly = score >= settings.fraud_anomaly_threshold or bool(rule_alerts)
        if is_anomaly and not rule_alerts:
            rule_alerts.append(AlertType.ANOMALOUS_PATTERN)
        return FraudPrediction(
            tx_id=tx.tx_id,
            anomaly_score=round(score, 4),
            is_anomaly=is_anomaly,
            triggered_rules=rule_alerts,
            model_version=self.model_version,
            computed_at=now_dt(),
        )

    def predict_batch(self, transactions: list[Transaction]) -> list[FraudPrediction]:
        if not transactions:
            return []
        df = pd.DataFrame([t.model_dump() for t in transactions])
        scores = self._score_raw(df)
        out = []
        for tx, s in zip(transactions, scores):
            rules = apply_rules(tx.model_dump())
            is_anom = float(s) >= settings.fraud_anomaly_threshold or bool(rules)
            if is_anom and not rules:
                rules.append(AlertType.ANOMALOUS_PATTERN)
            out.append(FraudPrediction(
                tx_id=tx.tx_id,
                anomaly_score=round(float(s), 4),
                is_anomaly=bool(is_anom),
                triggered_rules=rules,
                model_version=self.model_version,
                computed_at=now_dt(),
            ))
        return out

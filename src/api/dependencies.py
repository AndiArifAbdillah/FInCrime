"""Lazy singleton loaders for ML model instances used by the routes."""
from __future__ import annotations

from functools import lru_cache

from src.common.logger import get_logger

log = get_logger("api.deps")


@lru_cache(maxsize=1)
def get_risk_scorer():
    from src.layer0_risk_scoring import RiskScorer
    log.info("loading layer0 risk scorer")
    return RiskScorer()


@lru_cache(maxsize=1)
def get_fraud_detector():
    from src.layer1_fraud_detection import FraudDetector
    log.info("loading layer1 fraud detector")
    return FraudDetector()


@lru_cache(maxsize=1)
def get_crypto_tracer():
    from src.layer2_gnn_tracing import CryptoTracer
    log.info("loading layer2 crypto tracer")
    return CryptoTracer()


@lru_cache(maxsize=1)
def get_report_generator():
    from src.layer3_regtech import ReportGenerator
    log.info("loading layer3 report generator")
    return ReportGenerator()

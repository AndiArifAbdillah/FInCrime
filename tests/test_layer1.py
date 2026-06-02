"""Layer 1 — Fraud Detection smoke tests."""
import pytest

from src.layer1_fraud_detection.features import tx_features
from src.layer1_fraud_detection.rules import apply_rules
from src.common.schemas import AlertType


def test_features_present():
    import pandas as pd
    df = pd.DataFrame([{
        "amount_idr": 49_000_000,
        "channel": "bank",
        "sender_age_days": 100, "sender_tx_count_7d": 5,
        "is_high_risk_jurisdiction": True,
        "timestamp": "2026-05-21T10:00:00",
    }])
    X = tx_features(df)
    assert X.shape[0] == 1


def test_rule_smurfing_trigger():
    alerts = apply_rules({
        "amount_idr": 45_000_000,
        "is_high_risk_jurisdiction": False,
    })
    assert AlertType.SMURFING in alerts


def test_rule_high_risk_country():
    alerts = apply_rules({
        "amount_idr": 1_000,
        "is_high_risk_jurisdiction": True,
    })
    assert AlertType.HIGH_RISK_JURISDICTION in alerts


@pytest.mark.slow
def test_train_layer1(sample_dir, tmp_path):
    from src.layer1_fraud_detection.train import train
    meta = train(sample_dir / "transactions.csv", tmp_path, ae_epochs=3)
    assert meta["model_version"] == "0.1.0"

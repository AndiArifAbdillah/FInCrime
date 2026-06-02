"""Layer 0 — Risk Scoring smoke tests."""
import pytest

from src.layer0_risk_scoring.features import build_features
from src.layer0_risk_scoring.train import train


def test_build_features_columns():
    import pandas as pd
    df = pd.DataFrame([{
        "entity_id": "X", "entity_type": "individual", "country": "ID",
        "age_days": 100, "kyc_level": 1,
        "txn_count_30d": 10, "total_volume_30d": 1000, "avg_tx_amount": 100,
        "distinct_counterparties_30d": 5,
        "pep_flag": False, "sanction_flag": False, "has_crypto_activity": False,
    }])
    X = build_features(df)
    assert X.shape == (1, 17)


@pytest.mark.slow
def test_train_layer0(sample_dir, tmp_path):
    meta = train(sample_dir / "entities.csv", tmp_path)
    assert "metrics" in meta
    assert meta["metrics"]["roc_auc"] > 0.6

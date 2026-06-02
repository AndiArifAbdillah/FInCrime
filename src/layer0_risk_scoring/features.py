"""Feature engineering for entity-level risk scoring (Layer 0)."""
from __future__ import annotations

import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "age_days",
    "kyc_level",
    "txn_count_30d",
    "total_volume_30d",
    "avg_tx_amount",
    "distinct_counterparties_30d",
]
BOOLEAN_FEATURES = ["pep_flag", "sanction_flag", "has_crypto_activity"]
DERIVED_FEATURES = [
    "log_total_volume",
    "log_avg_amount",
    "velocity_30d",
    "counterparty_concentration",
    "is_high_risk_country",
    "is_corporate",
    "is_wallet",
    "low_kyc_high_volume",
]
ALL_FEATURES = NUMERIC_FEATURES + BOOLEAN_FEATURES + DERIVED_FEATURES

HIGH_RISK_COUNTRIES = {"KP", "IR", "MM", "AF", "SY", "VE"}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Take an entity DataFrame and produce the feature matrix used by XGBoost."""
    x = df.copy()

    # ensure required columns present
    for col in NUMERIC_FEATURES + BOOLEAN_FEATURES:
        if col not in x.columns:
            x[col] = 0

    # cast booleans to int
    for col in BOOLEAN_FEATURES:
        x[col] = x[col].astype(int)

    # derived
    x["log_total_volume"] = np.log1p(x["total_volume_30d"].clip(lower=0))
    x["log_avg_amount"] = np.log1p(x["avg_tx_amount"].clip(lower=0))
    x["velocity_30d"] = x["txn_count_30d"] / 30.0
    x["counterparty_concentration"] = (
        x["distinct_counterparties_30d"] / x["txn_count_30d"].clip(lower=1)
    )
    x["is_high_risk_country"] = x.get("country", pd.Series(["ID"] * len(x))).isin(
        HIGH_RISK_COUNTRIES
    ).astype(int)
    x["is_corporate"] = (x.get("entity_type", pd.Series(["individual"] * len(x))) == "corporate").astype(int)
    x["is_wallet"] = (x.get("entity_type", pd.Series(["individual"] * len(x))) == "wallet").astype(int)
    x["low_kyc_high_volume"] = (
        (x["kyc_level"] <= 1) & (x["total_volume_30d"] > 1e9)
    ).astype(int)

    return x[ALL_FEATURES].astype(float)

"""Transaction-level feature engineering for Layer 1."""
from __future__ import annotations

import numpy as np
import pandas as pd

TX_NUMERIC = [
    "amount_idr",
    "sender_age_days",
    "sender_tx_count_7d",
]
TX_DERIVED = [
    "log_amount",
    "amount_to_age_ratio",
    "is_cross_channel",
    "is_crypto",
    "is_bank",
    "is_ewallet",
    "is_high_risk_jurisdiction",
    "near_threshold_50m",
    "hour_of_day",
    "is_weekend",
]
ALL_TX_FEATURES = TX_NUMERIC + TX_DERIVED


def tx_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    # ensure present
    for c in TX_NUMERIC:
        if c not in x.columns:
            x[c] = 0

    x["sender_age_days"] = x["sender_age_days"].fillna(0)
    x["sender_tx_count_7d"] = x["sender_tx_count_7d"].fillna(0)

    x["log_amount"] = np.log1p(x["amount_idr"].clip(lower=0))
    x["amount_to_age_ratio"] = x["amount_idr"] / x["sender_age_days"].clip(lower=1)
    channel = x.get("channel", pd.Series(["bank"] * len(x)))
    x["is_crypto"] = (channel == "crypto").astype(int)
    x["is_bank"] = (channel == "bank").astype(int)
    x["is_ewallet"] = (channel == "ewallet").astype(int)
    x["is_cross_channel"] = (x["is_crypto"] & (~x["is_crypto"].shift(1).fillna(0).astype(bool))).astype(int)
    x["is_high_risk_jurisdiction"] = x.get("is_high_risk_jurisdiction",
                                            pd.Series([False] * len(x))).astype(int)
    # PPATK trigger lurks at IDR 500M (LTKT) / suspicious if just below it
    x["near_threshold_50m"] = ((x["amount_idr"] >= 40_000_000) &
                               (x["amount_idr"] <= 49_999_999)).astype(int)
    if "timestamp" in x.columns:
        ts = pd.to_datetime(x["timestamp"], errors="coerce")
        x["hour_of_day"] = ts.dt.hour.fillna(12).astype(int)
        x["is_weekend"] = (ts.dt.dayofweek >= 5).astype(int)
    else:
        x["hour_of_day"] = 12
        x["is_weekend"] = 0

    return x[ALL_TX_FEATURES].astype(float)

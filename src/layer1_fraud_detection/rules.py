"""Deterministic rule engine that complements the ML detectors."""
from __future__ import annotations


from src.common.schemas import AlertType


def apply_rules(tx: dict) -> list[AlertType]:
    """Return list of AlertType triggered by simple deterministic rules."""
    alerts: list[AlertType] = []
    amount = float(tx.get("amount_idr", 0))

    # Near-threshold smurfing (just below LTKM 50M IDR cash threshold)
    if 40_000_000 <= amount <= 49_999_999:
        alerts.append(AlertType.SMURFING)

    # Volume spike: amount >> sender's 7-day historical (rough heuristic)
    avg_recent = float(tx.get("sender_avg_amount_7d", 0) or 0)
    if avg_recent > 0 and amount >= avg_recent * 10 and amount > 100_000_000:
        alerts.append(AlertType.VOLUME_SPIKE)

    # High-risk jurisdiction
    if bool(tx.get("is_high_risk_jurisdiction", False)):
        alerts.append(AlertType.HIGH_RISK_JURISDICTION)

    # Blacklist sender or receiver
    if tx.get("sender_on_blacklist") or tx.get("receiver_on_blacklist"):
        alerts.append(AlertType.BLACKLIST_HIT)

    return alerts

"""Shared schema sanity tests."""
from datetime import datetime
from src.common.utils import utc_now

from src.common.schemas import Entity, Transaction, RiskLevel, Channel


def test_entity_defaults():
    e = Entity(entity_id="X", entity_type="individual")
    assert e.country == "ID"
    assert e.kyc_level == 0
    assert e.pep_flag is False


def test_transaction_amount_validation():
    tx = Transaction(
        tx_id="t1", channel=Channel.BANK,
        timestamp=utc_now(),
        sender_id="A", receiver_id="B",
        amount_idr=100_000,
    )
    assert tx.amount_idr == 100_000
    assert tx.currency == "IDR"


def test_risk_level_enum():
    assert RiskLevel.HIGH.value == "high"

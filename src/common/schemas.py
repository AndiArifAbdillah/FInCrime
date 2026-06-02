"""Shared Pydantic schemas across all layers."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ===================== Enums =====================
class Channel(str, Enum):
    BANK = "bank"
    EWALLET = "ewallet"
    CRYPTO = "crypto"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    SMURFING = "smurfing"
    LAYERING = "layering"
    VOLUME_SPIKE = "volume_spike"
    HIGH_RISK_JURISDICTION = "high_risk_jurisdiction"
    BLACKLIST_HIT = "blacklist_hit"
    ANOMALOUS_PATTERN = "anomalous_pattern"


# ===================== Inputs =====================
class Transaction(BaseModel):
    """Canonical transaction across all channels."""
    model_config = ConfigDict(use_enum_values=True)

    tx_id: str = Field(..., description="Globally unique transaction id")
    channel: Channel
    timestamp: datetime
    sender_id: str = Field(..., description="Account/wallet id of sender")
    receiver_id: str
    amount_idr: float = Field(..., gt=0, description="Amount normalized to IDR")
    currency: str = "IDR"
    country_from: str = "ID"
    country_to: str = "ID"
    # crypto-specific
    chain: Optional[str] = None   # eth, btc, bsc, polygon
    tx_hash: Optional[str] = None
    # context
    sender_age_days: Optional[int] = None
    sender_tx_count_7d: Optional[int] = None
    is_high_risk_jurisdiction: bool = False


class Entity(BaseModel):
    """Customer/wallet/account entity for risk scoring."""
    entity_id: str
    entity_type: str  # individual, corporate, wallet
    country: str = "ID"
    age_days: int = 0
    kyc_level: int = 0  # 0=none 1=basic 2=enhanced
    txn_count_30d: int = 0
    total_volume_30d: float = 0.0
    avg_tx_amount: float = 0.0
    distinct_counterparties_30d: int = 0
    pep_flag: bool = False           # politically exposed person
    sanction_flag: bool = False
    has_crypto_activity: bool = False


# ===================== Outputs =====================
class RiskScore(BaseModel):
    entity_id: str
    score: float = Field(..., ge=0, le=100)
    level: RiskLevel
    top_factors: list[dict] = Field(default_factory=list)  # SHAP
    model_version: str
    computed_at: datetime


class FraudPrediction(BaseModel):
    tx_id: str
    anomaly_score: float = Field(..., ge=0, le=1)
    is_anomaly: bool
    triggered_rules: list[AlertType] = Field(default_factory=list)
    model_version: str
    computed_at: datetime


class GraphTraceResult(BaseModel):
    seed_wallet: str
    subgraph_size: int
    layering_score: float = Field(..., ge=0, le=1)
    flagged_wallets: list[str]
    path_count: int
    max_hop: int
    pattern_types: list[AlertType]
    explanation: str


class Alert(BaseModel):
    alert_id: str
    tx_id: Optional[str] = None
    entity_id: Optional[str] = None
    alert_type: AlertType
    severity: RiskLevel
    score: float
    message: str
    raised_at: datetime
    layer: str  # layer0, layer1, layer2

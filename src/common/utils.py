"""Shared utility helpers."""
from __future__ import annotations

import hashlib
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .schemas import RiskLevel, Transaction, Entity
from .config import settings


def _clean_nan(v: Any) -> Any:
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def row_to_transaction(row: dict | Any) -> Transaction | None:
    """Build a Transaction from a dict / pandas Series, converting NaN -> None.

    Returns None if validation fails (e.g., missing required field).
    """
    payload = {}
    for k in Transaction.model_fields:
        if k not in row:
            continue
        payload[k] = _clean_nan(row[k])
    try:
        return Transaction(**payload)
    except Exception:
        return None


def rows_to_transactions(rows: Iterable[Any]) -> list[Transaction]:
    out: list[Transaction] = []
    for r in rows:
        tx = row_to_transaction(r)
        if tx is not None:
            out.append(tx)
    return out


def row_to_entity(row: dict | Any) -> Entity | None:
    payload = {}
    for k in Entity.model_fields:
        if k not in row:
            continue
        payload[k] = _clean_nan(row[k])
    try:
        return Entity(**payload)
    except Exception:
        return None


def utc_now() -> datetime:
    """Naive UTC now — drop-in replacement for the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def now_iso() -> str:
    return utc_now().isoformat()


def now_dt() -> datetime:
    return utc_now()


def make_id(prefix: str = "tx") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def risk_level_from_score(score: float) -> RiskLevel:
    if score >= settings.risk_score_critical:
        return RiskLevel.CRITICAL
    if score >= settings.risk_score_high:
        return RiskLevel.HIGH
    if score >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def model_path(name: str) -> Path:
    return settings.app_models_dir / name


def ensure_model_dir() -> Path:
    settings.app_models_dir.mkdir(parents=True, exist_ok=True)
    return settings.app_models_dir

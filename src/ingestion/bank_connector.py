"""Skeleton bank-core connector. Replace `fetch_recent` with real API calls."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

import pandas as pd

from src.common.logger import get_logger
from src.common.schemas import Transaction, Channel

log = get_logger("connector.bank")


class BankConnector:
    """In production: hits the partner bank's transaction API over OAuth2/mTLS.

    Here we read from a CSV snapshot for the prototype.
    """

    def __init__(self, csv_path: str | None = None):
        self.csv_path = csv_path

    def fetch_recent(self, since: datetime | None = None) -> Iterable[Transaction]:
        if not self.csv_path:
            log.info("bank.connector.no_path")
            return []
        df = pd.read_csv(self.csv_path)
        df = df[df["channel"] == "bank"]
        if since is not None:
            ts = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df[ts >= since]
        log.info("bank.connector.fetched", n=len(df))
        out: list[Transaction] = []
        for _, row in df.iterrows():
            try:
                out.append(Transaction(**{k: row[k] for k in Transaction.model_fields if k in row}))
            except Exception:
                continue
        return out

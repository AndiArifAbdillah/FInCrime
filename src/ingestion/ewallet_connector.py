"""Skeleton e-wallet (GoPay/OVO/Dana) connector."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd

from src.common.logger import get_logger
from src.common.schemas import Transaction

log = get_logger("connector.ewallet")


class EwalletConnector:
    def __init__(self, csv_path: str | None = None, provider: str = "GOPAY"):
        self.csv_path = csv_path
        self.provider = provider

    def fetch_recent(self, since: datetime | None = None) -> Iterable[Transaction]:
        if not self.csv_path:
            return []
        df = pd.read_csv(self.csv_path)
        df = df[df["channel"] == "ewallet"]
        if since is not None:
            ts = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df[ts >= since]
        log.info("ewallet.connector.fetched", provider=self.provider, n=len(df))
        out: list[Transaction] = []
        for _, row in df.iterrows():
            try:
                out.append(Transaction(**{k: row[k] for k in Transaction.model_fields if k in row}))
            except Exception:
                continue
        return out

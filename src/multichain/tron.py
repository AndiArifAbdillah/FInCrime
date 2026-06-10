"""Tron via TronGrid API.

API key (optional, gives higher rate limit): https://www.trongrid.io/
Without key: ~1 req/sec is OK for low-volume use.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from src.common.logger import get_logger
from .unified import ChainTransaction

log = get_logger("multichain.tron")

TRONGRID_BASE = "https://api.trongrid.io"


class TronConnector:
    def __init__(self, api_key: Optional[str] = None,
                 base_url: str = TRONGRID_BASE,
                 rate_limit_sec: float = 1.0,
                 trx_to_idr: float = 4_000.0):
        self.api_key = api_key or os.environ.get("TRONGRID_API_KEY", "")
        self.base_url = base_url
        self.rate_limit_sec = rate_limit_sec
        self.trx_to_idr = trx_to_idr
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self._last_call = time.monotonic()

    def fetch_address_transactions(self, address: str,
                                    limit: int = 50) -> list[ChainTransaction]:
        self._throttle()
        headers = {"User-Agent": "FinCrime-AI/0.1"}
        if self.api_key:
            headers["TRON-PRO-API-KEY"] = self.api_key
        try:
            with httpx.Client(timeout=15) as c:
                r = c.get(
                    f"{self.base_url}/v1/accounts/{address}/transactions",
                    params={"limit": limit},
                    headers=headers,
                )
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            log.warning("tron.fetch_failed", error=str(e))
            return []

        out: list[ChainTransaction] = []
        for tx in data.get("data", []):
            try:
                contract = (tx.get("raw_data", {}).get("contract") or [{}])[0]
                value = contract.get("parameter", {}).get("value", {})
                amt_sun = int(value.get("amount", 0))
                amt_trx = amt_sun / 1_000_000.0  # Sun to TRX
                sender = value.get("owner_address", "")
                receiver = value.get("to_address", "")
                ts = tx.get("block_timestamp", 0)
                out.append(ChainTransaction(
                    chain="tron",
                    tx_hash=tx.get("txID", ""),
                    timestamp=(datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                               .replace(tzinfo=None)) if ts else None,
                    sender=sender,
                    receiver=receiver,
                    amount_native=amt_trx,
                    amount_idr=amt_trx * self.trx_to_idr,
                    token_symbol="TRX",
                ))
            except Exception:
                continue
        log.info("tron.fetched", address=address[:10] + "...", n=len(out))
        return out

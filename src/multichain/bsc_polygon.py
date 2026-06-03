"""BNB Smart Chain (BSC) + Polygon — EVM-compatible chains.

Uses the Etherscan API V2 unified endpoint: ONE Etherscan API key works across
BSC, Polygon, and 60+ EVM chains by passing the chain ID. No separate BscScan /
PolygonScan key needed (those legacy V1 endpoints are being deprecated).

    - BSC     -> chainid 56
    - Polygon -> chainid 137
    Key: set ETHERSCAN_API_KEY in .env  (https://etherscan.io/myapikey)
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

import httpx

from src.common.config import settings
from src.common.logger import get_logger
from .unified import ChainTransaction

log = get_logger("multichain.bsc_polygon")

# Etherscan API V2 — single endpoint + chainid for all EVM chains.
ETHERSCAN_V2_BASE = "https://api.etherscan.io/v2/api"

CHAIN_CONFIG = {
    "bsc": {
        "chainid": 56,
        "key_env": "BSCSCAN_API_KEY",      # optional legacy fallback
        "native": "BNB",
        "to_idr": 9_500_000.0,             # placeholder rate
    },
    "polygon": {
        "chainid": 137,
        "key_env": "POLYGONSCAN_API_KEY",  # optional legacy fallback
        "native": "MATIC",
        "to_idr": 12_000.0,
    },
}


class BscPolygonConnector:
    def __init__(self, chain: str = "bsc", api_key: Optional[str] = None,
                 rate_limit_sec: float = 0.25):
        if chain not in CHAIN_CONFIG:
            raise ValueError(f"Unsupported chain {chain}")
        self.chain = chain
        cfg = CHAIN_CONFIG[chain]
        self.chainid = cfg["chainid"]
        self.native = cfg["native"]
        self.to_idr = cfg["to_idr"]
        # Etherscan API V2: one key for all chains. Prefer ETHERSCAN_API_KEY;
        # fall back to a chain-specific legacy key only if explicitly set.
        self.api_key = (api_key or settings.etherscan_api_key
                        or os.environ.get(cfg["key_env"], ""))
        self.rate_limit_sec = rate_limit_sec
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self._last_call = time.monotonic()

    def _get(self, params: dict, timeout: int = 15) -> dict:
        if not self.api_key:
            log.warning(f"{self.chain}.no_api_key — set ETHERSCAN_API_KEY in .env "
                        "(Etherscan API V2 covers BSC/Polygon with one key)")
            return {"status": "0", "result": []}
        params = {**params, "chainid": self.chainid, "apikey": self.api_key}
        self._throttle()
        with httpx.Client(timeout=timeout) as c:
            r = c.get(ETHERSCAN_V2_BASE, params=params)
            r.raise_for_status()
            return r.json()

    def fetch_address_transactions(self, address: str,
                                    limit: int = 50) -> list[ChainTransaction]:
        data = self._get({
            "module": "account", "action": "txlist",
            "address": address,
            "page": 1, "offset": limit, "sort": "desc",
        })
        if str(data.get("status")) != "1":
            return []
        out: list[ChainTransaction] = []
        for t in data.get("result", []):
            try:
                value = float(t.get("value", 0)) / 1e18
                out.append(ChainTransaction(
                    chain=self.chain,
                    tx_hash=t.get("hash", ""),
                    block_height=int(t.get("blockNumber", 0)) or None,
                    timestamp=datetime.utcfromtimestamp(int(t.get("timeStamp", 0))),
                    sender=t.get("from", "").lower(),
                    receiver=t.get("to", "").lower(),
                    amount_native=value,
                    amount_idr=value * self.to_idr,
                    token_symbol=self.native,
                    fee_native=float(t.get("gasUsed", 0)) * float(t.get("gasPrice", 0)) / 1e18,
                ))
            except Exception:
                continue
        log.info(f"{self.chain}.fetched", address=address[:10] + "...", n=len(out))
        return out

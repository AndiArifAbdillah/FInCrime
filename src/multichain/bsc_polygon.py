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
from datetime import datetime, timezone
from typing import Optional

import httpx

from src.common.config import settings
from src.common.logger import get_logger
from .unified import ChainTransaction

log = get_logger("multichain.bsc_polygon")

# Etherscan API V2 — single endpoint + chainid for all EVM chains.
ETHERSCAN_V2_BASE = "https://api.etherscan.io/v2/api"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

CHAIN_CONFIG = {
    "bsc": {
        "chainid": 56,
        "key_env": "BSCSCAN_API_KEY",      # optional legacy fallback
        "native": "BNB",
        "coingecko_id": "binancecoin",
        "to_idr_fallback": 9_500_000.0,    # used only if CoinGecko unreachable
    },
    "polygon": {
        "chainid": 137,
        "key_env": "POLYGONSCAN_API_KEY",  # optional legacy fallback
        # Polygon migrated its gas token MATIC -> POL (Sep 2024); the old
        # "matic-network" CoinGecko id now returns an empty object.
        "native": "POL",
        "coingecko_id": "polygon-ecosystem-token",
        "to_idr_fallback": 1_400.0,
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
        self.coingecko_id = cfg["coingecko_id"]
        self.to_idr_fallback = cfg["to_idr_fallback"]
        # Etherscan API V2: one key for all chains. Prefer ETHERSCAN_API_KEY;
        # fall back to a chain-specific legacy key only if explicitly set.
        self.api_key = (api_key or settings.etherscan_api_key
                        or os.environ.get(cfg["key_env"], ""))
        self.rate_limit_sec = rate_limit_sec
        self._last_call = 0.0
        self._idr_cache: Optional[float] = None
        self._idr_cache_ts: float = 0.0

    def _throttle(self):
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self._last_call = time.monotonic()

    def to_idr_rate(self, timeout: int = 8) -> float:
        """Live native→IDR rate from CoinGecko, cached 5 minutes.

        Falls back to a static rate when CoinGecko is unreachable (offline demo).
        """
        if self._idr_cache and (time.time() - self._idr_cache_ts) < 300:
            return self._idr_cache
        try:
            with httpx.Client(timeout=timeout) as c:
                r = c.get(f"{COINGECKO_BASE}/simple/price",
                          params={"ids": self.coingecko_id, "vs_currencies": "idr"})
                r.raise_for_status()
                rate = float(r.json()[self.coingecko_id]["idr"])
                self._idr_cache = rate
                self._idr_cache_ts = time.time()
                log.info(f"{self.chain}.to_idr_live", rate=rate)
                return rate
        except Exception as e:
            log.warning(f"{self.chain}.coingecko_fallback", error=str(e))
            self._idr_cache = self.to_idr_fallback
            self._idr_cache_ts = time.time()
            return self.to_idr_fallback

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
        to_idr = self.to_idr_rate()
        out: list[ChainTransaction] = []
        for t in data.get("result", []):
            try:
                value = float(t.get("value", 0)) / 1e18
                ts = datetime.fromtimestamp(int(t.get("timeStamp", 0)),
                                            tz=timezone.utc).replace(tzinfo=None)
                out.append(ChainTransaction(
                    chain=self.chain,
                    tx_hash=t.get("hash", ""),
                    block_height=int(t.get("blockNumber", 0)) or None,
                    timestamp=ts,
                    sender=t.get("from", "").lower(),
                    receiver=t.get("to", "").lower(),
                    amount_native=value,
                    amount_idr=value * to_idr,
                    token_symbol=self.native,
                    fee_native=float(t.get("gasUsed", 0)) * float(t.get("gasPrice", 0)) / 1e18,
                ))
            except Exception:
                continue
        log.info(f"{self.chain}.fetched", address=address[:10] + "...", n=len(out))
        return out

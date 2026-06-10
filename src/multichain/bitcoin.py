"""Bitcoin via Blockstream Esplora API — FREE, no API key needed."""
from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx

from src.common.logger import get_logger
from .unified import ChainTransaction

log = get_logger("multichain.btc")

ESPLORA_BASE = "https://blockstream.info/api"


class BitcoinConnector:
    """Wraps Blockstream Esplora. Public, free, no key.

    Docs: https://github.com/Blockstream/esplora/blob/master/API.md
    """

    def __init__(self, base_url: str = ESPLORA_BASE, rate_limit_sec: float = 0.2,
                 btc_to_idr: float = 1_700_000_000.0):
        self.base_url = base_url
        self.rate_limit_sec = rate_limit_sec
        self.btc_to_idr = btc_to_idr  # fallback rate
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self._last_call = time.monotonic()

    def _get(self, path: str, timeout: int = 15) -> dict | list:
        self._throttle()
        with httpx.Client(timeout=timeout) as c:
            r = c.get(f"{self.base_url}{path}",
                      headers={"User-Agent": "FinCrime-AI/0.1"})
            r.raise_for_status()
            return r.json()

    def get_address_info(self, address: str) -> dict:
        return self._get(f"/address/{address}")

    def fetch_address_transactions(self, address: str,
                                    limit: int = 50) -> list[ChainTransaction]:
        """Returns the last `limit` transactions involving `address`."""
        try:
            raw = self._get(f"/address/{address}/txs")
        except Exception as e:
            log.warning("btc.fetch_failed", address=address[:10], error=str(e))
            return []
        out: list[ChainTransaction] = []
        for tx in raw[:limit]:
            # Find dominant in/out involving our address
            sender, receiver = "", ""
            value_sats = 0
            for vin in tx.get("vin", []):
                prev_out = vin.get("prevout") or {}
                if prev_out.get("scriptpubkey_address") and not sender:
                    sender = prev_out["scriptpubkey_address"]
            for vout in tx.get("vout", []):
                if vout.get("scriptpubkey_address") == address:
                    value_sats += int(vout.get("value", 0))
                    receiver = address
                elif not receiver and vout.get("scriptpubkey_address"):
                    receiver = vout["scriptpubkey_address"]
                    value_sats = int(vout.get("value", 0))

            value_btc = value_sats / 1e8
            ts = None
            if tx.get("status", {}).get("block_time"):
                ts = datetime.fromtimestamp(int(tx["status"]["block_time"]),
                                            tz=timezone.utc).replace(tzinfo=None)

            out.append(ChainTransaction(
                chain="btc",
                tx_hash=tx.get("txid", ""),
                block_height=tx.get("status", {}).get("block_height"),
                timestamp=ts,
                sender=sender,
                receiver=receiver or address,
                amount_native=value_btc,
                amount_idr=value_btc * self.btc_to_idr,
                fee_native=tx.get("fee", 0) / 1e8,
            ))
        log.info("btc.fetched", address=address[:10] + "...", n=len(out))
        return out

    def get_balance_btc(self, address: str) -> float:
        info = self.get_address_info(address)
        chain = info.get("chain_stats", {})
        funded = chain.get("funded_txo_sum", 0)
        spent = chain.get("spent_txo_sum", 0)
        return (funded - spent) / 1e8

"""Blockchain RPC connector — Etherscan REST + optional web3 RPC.

The Etherscan v2 API gives free 5 req/s, 100k req/day with an API key.
Get a key here: https://etherscan.io/myapikey
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import httpx

from src.common.config import settings
from src.common.logger import get_logger
from src.common.schemas import Transaction, Channel
from src.common.utils import make_id

log = get_logger("connector.blockchain")

# ETH ↔ IDR — fetched live; falls back to a sane recent constant.
ETH_TO_USD_FALLBACK = 3500.0       # USD per ETH (mid-2026)
USD_TO_IDR_FALLBACK = 16_300.0     # IDR per USD


class BlockchainConnector:
    """Wraps the Etherscan v1 REST API + optional web3 RPC.

    Free tier: 5 calls/second, 100k/day. We add a 0.25s delay between calls.
    """

    ETHERSCAN_BASE = "https://api.etherscan.io/api"
    COINGECKO_BASE = "https://api.coingecko.com/api/v3"

    def __init__(self, etherscan_key: Optional[str] = None,
                 rpc_url: Optional[str] = None,
                 rate_limit_sec: float = 0.25):
        self.etherscan_key = etherscan_key or settings.etherscan_api_key
        self.rpc_url = rpc_url or settings.eth_rpc_url
        self.rate_limit_sec = rate_limit_sec
        self._last_call = 0.0
        self._eth_to_idr_cache: Optional[float] = None
        self._cache_ts: float = 0.0

        self._web3 = None
        if self.rpc_url:
            try:
                from web3 import Web3
                self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))
                log.info("blockchain.web3.connected",
                         chain_id=self._web3.eth.chain_id)
            except Exception as e:
                log.warning("blockchain.web3.unavailable", error=str(e))

    # --------------- internals ---------------
    def _throttle(self):
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self._last_call = time.monotonic()

    def _etherscan_get(self, params: dict, timeout: int = 15) -> dict:
        if not self.etherscan_key:
            raise RuntimeError("ETHERSCAN_API_KEY missing in .env")
        params = {**params, "apikey": self.etherscan_key}
        self._throttle()
        with httpx.Client(timeout=timeout) as client:
            r = client.get(self.ETHERSCAN_BASE, params=params)
            r.raise_for_status()
            data = r.json()
        if str(data.get("status")) != "1" and data.get("message") not in ("No transactions found", "OK"):
            log.warning("etherscan.error", message=data.get("message"),
                        result=str(data.get("result"))[:200])
        return data

    # --------------- price feed ---------------
    def get_eth_to_idr(self, timeout: int = 8) -> float:
        """Fetch live ETH → IDR rate from CoinGecko. Cached for 5 minutes."""
        if self._eth_to_idr_cache and (time.time() - self._cache_ts) < 300:
            return self._eth_to_idr_cache
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.get(
                    f"{self.COINGECKO_BASE}/simple/price",
                    params={"ids": "ethereum", "vs_currencies": "idr"},
                )
                r.raise_for_status()
                rate = float(r.json()["ethereum"]["idr"])
                self._eth_to_idr_cache = rate
                self._cache_ts = time.time()
                log.info("blockchain.eth_to_idr_live", rate=rate)
                return rate
        except Exception as e:
            log.warning("blockchain.coingecko_fallback", error=str(e))
            fallback = ETH_TO_USD_FALLBACK * USD_TO_IDR_FALLBACK
            self._eth_to_idr_cache = fallback
            self._cache_ts = time.time()
            return fallback

    @staticmethod
    def _wei_to_eth(wei: str | int) -> float:
        return int(wei) / 1e18

    # --------------- core fetch ---------------
    def fetch_address_transfers(self, address: str,
                                start_block: int = 0,
                                end_block: int = 99_999_999,
                                limit: int = 100) -> list[Transaction]:
        """Fetch normal ETH transactions for an address. Returns canonical Transactions."""
        data = self._etherscan_get({
            "module": "account", "action": "txlist",
            "address": address,
            "startblock": start_block, "endblock": end_block,
            "page": 1, "offset": limit, "sort": "desc",
        })
        if str(data.get("status")) != "1":
            return []

        rate = self.get_eth_to_idr()
        out: list[Transaction] = []
        for t in data.get("result", []):
            try:
                eth_amt = self._wei_to_eth(t["value"])
                if eth_amt <= 0:
                    continue
                out.append(Transaction(
                    tx_id=t["hash"],
                    channel=Channel.CRYPTO,
                    timestamp=datetime.utcfromtimestamp(int(t["timeStamp"])),
                    sender_id=f"WALLET_{t['from'].lower()}",
                    receiver_id=f"WALLET_{t['to'].lower()}",
                    amount_idr=round(eth_amt * rate, 2),
                    currency="ETH",
                    chain="eth",
                    tx_hash=t["hash"],
                    country_from="XX",
                    country_to="XX",
                ))
            except Exception as e:
                log.debug("etherscan.skip_tx", error=str(e))
                continue
        log.info("etherscan.fetched", address=address[:10] + "...", n=len(out))
        return out

    def fetch_token_transfers(self, address: str,
                              contract: Optional[str] = None,
                              limit: int = 100) -> list[Transaction]:
        """Fetch ERC-20 token transfers. Currently treats USDT/USDC ~ IDR via stablecoin assumption."""
        params = {
            "module": "account", "action": "tokentx",
            "address": address,
            "page": 1, "offset": limit, "sort": "desc",
        }
        if contract:
            params["contractaddress"] = contract
        data = self._etherscan_get(params)
        if str(data.get("status")) != "1":
            return []

        usd_to_idr = USD_TO_IDR_FALLBACK
        out: list[Transaction] = []
        for t in data.get("result", []):
            try:
                decimals = int(t.get("tokenDecimal", "18"))
                raw = int(t["value"])
                amount = raw / (10 ** decimals)
                symbol = t.get("tokenSymbol", "")
                # crude IDR conversion: stablecoins → 1:1 USD, else skip
                if symbol.upper() in {"USDT", "USDC", "BUSD", "DAI"}:
                    idr = amount * usd_to_idr
                else:
                    # unknown token — keep raw amount, mark as unknown
                    idr = amount
                out.append(Transaction(
                    tx_id=t["hash"] + "_" + str(t.get("transactionIndex", "0")),
                    channel=Channel.CRYPTO,
                    timestamp=datetime.utcfromtimestamp(int(t["timeStamp"])),
                    sender_id=f"WALLET_{t['from'].lower()}",
                    receiver_id=f"WALLET_{t['to'].lower()}",
                    amount_idr=round(idr, 2),
                    currency=symbol or "ETH",
                    chain="eth",
                    tx_hash=t["hash"],
                ))
            except Exception:
                continue
        log.info("etherscan.token_fetched", address=address[:10] + "...", n=len(out))
        return out

    # --------------- balance & summary ---------------
    def get_eth_balance(self, address: str) -> float:
        data = self._etherscan_get({
            "module": "account", "action": "balance",
            "address": address, "tag": "latest",
        })
        if str(data.get("status")) != "1":
            return 0.0
        return self._wei_to_eth(data["result"])

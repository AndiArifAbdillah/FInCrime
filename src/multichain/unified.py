"""Unified multi-chain interface."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.common.logger import get_logger

log = get_logger("multichain.unified")


@dataclass
class ChainTransaction:
    """Canonical cross-chain transaction representation."""
    chain: str                         # "btc" | "eth" | "bsc" | "polygon" | "tron"
    tx_hash: str
    block_height: Optional[int] = None
    timestamp: Optional[datetime] = None
    sender: str = ""
    receiver: str = ""
    amount_native: float = 0.0         # in native token (BTC, ETH, BNB, MATIC, TRX)
    amount_idr: float = 0.0
    token_symbol: str = ""             # for ERC-20/BEP-20/TRC-20 transfers
    is_token_transfer: bool = False
    fee_native: float = 0.0


def detect_chain_from_address(address: str) -> Optional[str]:
    """Heuristic: detect blockchain from address format."""
    if not address:
        return None
    addr = address.strip()
    # EVM (Ethereum, BSC, Polygon — same format)
    if re.match(r"^0x[a-fA-F0-9]{40}$", addr):
        return "evm"
    # Bitcoin Legacy (P2PKH) — starts with 1, 25-34 chars
    if re.match(r"^1[a-km-zA-HJ-NP-Z1-9]{25,34}$", addr):
        return "btc"
    # Bitcoin Segwit-P2SH (starts with 3)
    if re.match(r"^3[a-km-zA-HJ-NP-Z1-9]{25,34}$", addr):
        return "btc"
    # Bitcoin Bech32 (Native SegWit, starts with bc1)
    if re.match(r"^bc1[a-zA-HJ-NP-Z0-9]{25,87}$", addr):
        return "btc"
    # Tron — starts with T
    if re.match(r"^T[a-km-zA-HJ-NP-Z1-9]{33}$", addr):
        return "tron"
    return None


class UnifiedChainConnector:
    """Dispatches wallet queries to the right chain connector."""

    def __init__(self):
        self._btc = None
        self._bsc = None
        self._polygon = None
        self._tron = None
        self._eth = None

    def _get(self, chain: str):
        chain = chain.lower()
        if chain == "btc":
            if self._btc is None:
                from .bitcoin import BitcoinConnector
                self._btc = BitcoinConnector()
            return self._btc
        if chain == "bsc":
            if self._bsc is None:
                from .bsc_polygon import BscPolygonConnector
                self._bsc = BscPolygonConnector(chain="bsc")
            return self._bsc
        if chain == "polygon":
            if self._polygon is None:
                from .bsc_polygon import BscPolygonConnector
                self._polygon = BscPolygonConnector(chain="polygon")
            return self._polygon
        if chain == "tron":
            if self._tron is None:
                from .tron import TronConnector
                self._tron = TronConnector()
            return self._tron
        if chain == "eth":
            if self._eth is None:
                from src.ingestion.blockchain_connector import BlockchainConnector
                self._eth = BlockchainConnector()
            return self._eth
        raise ValueError(f"Unsupported chain: {chain}")

    def fetch_wallet_txs(self, chain: str, address: str,
                        limit: int = 50) -> list[ChainTransaction]:
        """Fetch transactions; never raises — returns [] on any failure."""
        try:
            conn = self._get(chain)
        except Exception as e:
            log.warning("multichain.no_connector", chain=chain, error=str(e))
            return []

        # Some connectors use 'fetch_address_transactions', others use the legacy
        # 'fetch_address_transfers'. Try both.
        fetch_method = (
            getattr(conn, "fetch_address_transactions", None)
            or getattr(conn, "fetch_address_transfers", None)
        )
        if fetch_method is None:
            log.warning("multichain.no_fetch_method", chain=chain)
            return []

        try:
            result = fetch_method(address, limit=limit)
        except Exception as e:
            # Common: ETHERSCAN_API_KEY missing, BscScan rate limit, network timeout
            log.warning("multichain.fetch_failed", chain=chain,
                        error=str(e)[:200])
            return []

        # Normalize result to list[ChainTransaction]
        # BlockchainConnector (legacy ETH) returns list[Transaction] (Pydantic),
        # not list[ChainTransaction]. Convert if needed.
        if not result:
            return []

        first = result[0]
        # If already ChainTransaction, return as-is
        if isinstance(first, ChainTransaction):
            return result

        # Convert legacy Pydantic Transaction → ChainTransaction
        normalized = []
        for tx in result:
            try:
                normalized.append(ChainTransaction(
                    chain=getattr(tx, "chain", None) or chain,
                    tx_hash=getattr(tx, "tx_hash", None) or getattr(tx, "tx_id", ""),
                    timestamp=getattr(tx, "timestamp", None),
                    sender=getattr(tx, "sender_id", "").replace("WALLET_", ""),
                    receiver=getattr(tx, "receiver_id", "").replace("WALLET_", ""),
                    amount_native=0.0,
                    amount_idr=float(getattr(tx, "amount_idr", 0)),
                    token_symbol=getattr(tx, "currency", "") or "",
                ))
            except Exception:
                continue
        return normalized

    def auto_detect_and_fetch(self, address: str,
                               limit: int = 50) -> tuple[Optional[str], list[ChainTransaction]]:
        """Detect chain from address format and fetch. Never raises."""
        chain = detect_chain_from_address(address)
        if chain is None:
            return None, []
        # 'evm' could be ETH, BSC, or Polygon — try ETH first as default
        chains_to_try = ["eth", "bsc", "polygon"] if chain == "evm" else [chain]
        last_chain = chains_to_try[0]
        for c in chains_to_try:
            try:
                txs = self.fetch_wallet_txs(c, address, limit=limit)
            except Exception as e:
                log.warning("multichain.auto_chain_failed", chain=c, error=str(e)[:200])
                continue
            last_chain = c
            if txs:
                return c, txs
        return last_chain, []

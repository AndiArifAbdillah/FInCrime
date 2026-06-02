"""Multi-chain crypto support.

Unified interface to query wallet transactions across chains:
    - Ethereum (existing layer 2 — handled by src.ingestion.blockchain_connector)
    - Bitcoin via Blockstream Esplora API (FREE, no API key)
    - BNB Smart Chain via BscScan (free API key)
    - Polygon via PolygonScan (free API key)
    - Tron via TronGrid (free API key)
"""
from .unified import (
    UnifiedChainConnector, ChainTransaction, detect_chain_from_address,
)
from .bitcoin import BitcoinConnector
from .bsc_polygon import BscPolygonConnector
from .tron import TronConnector

__all__ = [
    "UnifiedChainConnector", "ChainTransaction",
    "detect_chain_from_address",
    "BitcoinConnector", "BscPolygonConnector", "TronConnector",
]

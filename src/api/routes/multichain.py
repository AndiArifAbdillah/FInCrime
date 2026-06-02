"""Multi-chain crypto endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query

from src.multichain import (
    UnifiedChainConnector, detect_chain_from_address,
)

router = APIRouter()
_unified = UnifiedChainConnector()


@router.get("/v1/multichain/detect/{address}")
def detect_chain(address: str):
    return {"address": address, "chain": detect_chain_from_address(address)}


@router.get("/v1/multichain/{chain}/wallet/{address}/txs")
def wallet_txs(chain: str, address: str, limit: int = Query(20, ge=1, le=200)):
    txs = _unified.fetch_wallet_txs(chain, address, limit=limit)
    return {
        "chain": chain,
        "address": address,
        "count": len(txs),
        "txs": [t.__dict__ for t in txs],
    }


@router.get("/v1/multichain/auto/{address}")
def auto_trace(address: str, limit: int = Query(20, ge=1, le=200)):
    chain, txs = _unified.auto_detect_and_fetch(address, limit=limit)
    return {
        "address": address,
        "detected_chain": chain,
        "count": len(txs),
        "txs": [t.__dict__ for t in txs],
    }


# ============================================================
# Privacy Coin Monitoring (Monero / Zcash / Dash)
# ============================================================
@router.get("/v1/privacy-coin/matrix")
def privacy_coin_matrix():
    """3-tier traceability matrix — Transparent / Obfuscated / Privacy Coin."""
    from src.multichain.privacy_coin_monitor import coverage_matrix
    return {"matrix": coverage_matrix()}


@router.get("/v1/privacy-coin/info/{symbol}")
def privacy_coin_info_endpoint(symbol: str):
    """Info edukatif satu privacy coin (Monero/Zcash/Dash)."""
    from src.multichain.privacy_coin_monitor import privacy_coin_info
    return privacy_coin_info(symbol)


@router.get("/v1/privacy-coin/check/{chain}/{address}")
def privacy_coin_check(chain: str, address: str,
                       limit: int = Query(50, ge=1, le=200)):
    """Periksa apakah wallet terindikasi konversi ke/dari privacy coin.

    Mengambil transaksi wallet, lalu deteksi pola on/off-ramp ke exchange
    pendukung privacy coin. TIDAK mengklaim trace internal Monero — hanya
    monitor pintu masuk/keluar (standar industri).
    """
    from src.multichain.privacy_coin_monitor import check_address_for_privacy_coin
    txs = _unified.fetch_wallet_txs(chain, address, limit=limit)
    flag = check_address_for_privacy_coin(address, txs)
    if flag is None:
        return {
            "address": address,
            "chain": chain,
            "flagged": False,
            "message": "Tidak terdeteksi interaksi dengan exchange privacy coin.",
            "txs_checked": len(txs),
        }
    return {
        "address": address,
        "chain": chain,
        "flagged": True,
        "flag": flag.__dict__,
        "txs_checked": len(txs),
    }

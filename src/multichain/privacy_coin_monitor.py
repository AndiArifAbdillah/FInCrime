"""Privacy Coin Monitor — deteksi & flagging Monero/Zcash/Dash.

PENTING — KEBENARAN TEKNIS:
    Privacy coin (Monero/Zcash shielded/Dash PrivateSend) TIDAK BISA di-trace
    internal-nya oleh siapa pun, termasuk Chainalysis/Elliptic/TRM Labs. Ini
    bukan keterbatasan kami, tapi memang dirancang anonim secara kriptografis
    (ring signatures, stealth addresses, RingCT, zk-SNARKs).

STRATEGI YANG DIPAKAI (sama dengan standar industri global):
    "Trace the on/off-ramp" — kita TIDAK klaim bisa lihat transaksi internal
    Monero. Yang kita lakukan:
      1. Deteksi wallet transparent (BTC/ETH) yang KIRIM dana ke exchange
         pendukung privacy coin (on-ramp) → flag "potential privacy coin entry".
      2. Deteksi dana yang KELUAR dari exchange privacy coin kembali ke fiat/
         stablecoin (off-ramp) → flag "potential privacy coin exit".
      3. Behavioral fingerprint: pola konversi cepat ETH→XMR→USDT.
      4. Auto-flag karena Bappebti TIDAK mengizinkan privacy coin di Indonesia —
         sehingga transaksi privacy coin di yurisdiksi ID sudah suspicious
         dengan sendirinya.

REGULASI:
    - Bappebti: Monero, Zcash, Dash TIDAK ada di daftar 501 aset kripto resmi
    - FATF Rec 16 (Travel Rule): VASP wajib share info pengirim/penerima
    - EU MiCA 2024: privacy coin dilarang di regulated exchange
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.common.logger import get_logger

log = get_logger("multichain.privacy_coin")


# ============================================================
# Privacy coin yang dimonitor
# ============================================================
class PrivacyCoin(str, Enum):
    MONERO = "XMR"
    ZCASH = "ZEC"
    DASH = "DASH"
    PIRATE = "ARRR"
    BEAM = "BEAM"
    GRIN = "GRIN"


# Tingkat privacy (makin tinggi makin sulit di-trace)
PRIVACY_LEVEL = {
    "XMR": 5,    # Monero — paling private (ring sig + RingCT + stealth)
    "ARRR": 5,   # Pirate Chain — full zk-SNARK
    "ZEC": 4,    # Zcash — shielded (z-addr) full, t-addr transparent
    "BEAM": 4,   # Mimblewimble
    "GRIN": 4,   # Mimblewimble
    "DASH": 2,   # Dash PrivateSend — coinjoin-based, masih bisa partial
}


# ============================================================
# Exchange yang mendukung privacy coin (on/off-ramp points)
# Sumber: public listing data per 2024-2025.
# Kontrak/hot-wallet ETH dari exchange ini = sinyal on/off-ramp.
# ============================================================
# Catatan: ini contoh hot-wallet exchange yang HISTORIS dukung privacy coin.
# Dalam produksi, list ini di-maintain & di-update dari intel feed.
PRIVACY_COIN_EXCHANGES = {
    # address (lowercase) -> (nama exchange, coins didukung)
    "0x28c6c06298d514db089934071355e5743bf21d60": ("Binance (hist. XMR/ZEC/DASH)", ["XMR", "ZEC", "DASH"]),
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": ("Binance 2", ["XMR", "ZEC", "DASH"]),
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": ("Binance 3", ["XMR", "ZEC", "DASH"]),
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": ("Kraken (XMR/ZEC/DASH)", ["XMR", "ZEC", "DASH"]),
    "0xa910f92acdaf488fa6ef02174fb86208ad7722ba": ("Poloniex (XMR/ZEC)", ["XMR", "ZEC"]),
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": ("Gate.io (XMR/ZEC/DASH)", ["XMR", "ZEC", "DASH"]),
    "0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98": ("Bittrex (hist.)", ["XMR", "ZEC", "DASH"]),
}

# Bappebti — daftar aset kripto yang DIIZINKAN di Indonesia TIDAK termasuk ini.
BAPPEBTI_FORBIDDEN = {"XMR", "ZEC", "DASH", "ARRR", "BEAM", "GRIN"}


@dataclass
class PrivacyCoinFlag:
    wallet: str
    flag_type: str            # "on_ramp" | "off_ramp" | "direct_holding" | "rapid_conversion"
    severity: str             # "low" | "medium" | "high" | "critical"
    score: float              # 0-1
    coins_involved: list[str]
    exchange: str = ""
    message: str = ""
    indicators: list[str] = field(default_factory=list)


# ============================================================
# Core detection
# ============================================================
def check_address_for_privacy_coin(
    address: str,
    transactions: list | None = None,
) -> PrivacyCoinFlag | None:
    """Periksa apakah wallet transparent terindikasi konversi ke/dari privacy coin.

    Args:
        address: alamat wallet (EVM/BTC)
        transactions: list ChainTransaction (opsional) untuk analisis on/off-ramp

    Returns:
        PrivacyCoinFlag jika terindikasi, None jika bersih.
    """
    address_l = address.lower()
    indicators: list[str] = []
    coins: set[str] = set()
    exchange_name = ""
    on_ramp = False
    off_ramp = False

    transactions = transactions or []

    for tx in transactions:
        # Ambil counterparty (sender/receiver)
        sender = (getattr(tx, "sender", "") or "").lower()
        receiver = (getattr(tx, "receiver", "") or "").lower()

        # Cek apakah counterparty adalah exchange privacy coin
        for cp, is_outgoing in [(receiver, True), (sender, False)]:
            if cp in PRIVACY_COIN_EXCHANGES:
                ex_name, ex_coins = PRIVACY_COIN_EXCHANGES[cp]
                exchange_name = ex_name
                coins.update(ex_coins)
                if is_outgoing:
                    on_ramp = True
                    indicators.append(f"Transfer KE exchange pendukung privacy coin ({ex_name})")
                else:
                    off_ramp = True
                    indicators.append(f"Terima dana DARI exchange pendukung privacy coin ({ex_name})")

    if not (on_ramp or off_ramp):
        return None

    # Tentukan tipe & severity
    if on_ramp and off_ramp:
        flag_type = "rapid_conversion"
        severity = "critical"
        score = 0.9
        msg = ("Pola konversi bolak-balik ke/dari exchange privacy coin terdeteksi. "
               "Indikasi kuat upaya menyamarkan jejak dana via privacy coin.")
    elif on_ramp:
        flag_type = "on_ramp"
        severity = "high"
        score = 0.75
        msg = ("Dana dikirim ke exchange yang mendukung privacy coin (Monero/Zcash). "
               "Kemungkinan konversi ke aset anonim untuk memutus jejak.")
    else:
        flag_type = "off_ramp"
        severity = "high"
        score = 0.7
        msg = ("Dana diterima dari exchange privacy coin. "
               "Kemungkinan pencairan hasil dari aset anonim.")

    # Bappebti: privacy coin tidak diizinkan di Indonesia
    forbidden = sorted(coins & BAPPEBTI_FORBIDDEN)
    if forbidden:
        indicators.append(
            f"Privacy coin {', '.join(forbidden)} TIDAK termasuk daftar aset "
            "kripto resmi Bappebti — transaksi ini melanggar ketentuan PFAK."
        )

    return PrivacyCoinFlag(
        wallet=address,
        flag_type=flag_type,
        severity=severity,
        score=score,
        coins_involved=sorted(coins),
        exchange=exchange_name,
        message=msg,
        indicators=indicators,
    )


def is_privacy_coin_exchange(address: str) -> dict | None:
    """Cek apakah sebuah alamat adalah exchange pendukung privacy coin."""
    info = PRIVACY_COIN_EXCHANGES.get(address.lower())
    if not info:
        return None
    name, coins = info
    return {"exchange": name, "supported_privacy_coins": coins}


def privacy_coin_info(symbol: str) -> dict:
    """Info edukatif tentang sebuah privacy coin."""
    symbol = symbol.upper()
    level = PRIVACY_LEVEL.get(symbol, 0)
    traceable = level < 3
    return {
        "symbol": symbol,
        "privacy_level": level,                       # 0-5
        "internally_traceable": traceable,
        "bappebti_allowed": symbol not in BAPPEBTI_FORBIDDEN,
        "note": (
            "TIDAK dapat di-trace internal oleh tools manapun (termasuk "
            "Chainalysis/Elliptic). Strategi: monitor on/off-ramp."
            if not traceable else
            "Sebagian dapat di-trace (privacy opsional)."
        ),
    }


def coverage_matrix() -> list[dict]:
    """3-tier traceability matrix — untuk ditampilkan di UI / laporan."""
    return [
        {
            "tier": 1, "label": "Transparent",
            "coins": ["BTC", "ETH", "BSC", "Polygon", "Tron"],
            "traceable": "Penuh",
            "fincrime_capability": "Layer 2 GraphSAGE lacak alamat & layering chains",
            "color": "#22c55e",
        },
        {
            "tier": 2, "label": "Obfuscated (Mixer)",
            "coins": ["Tornado Cash", "CoinJoin", "Wasabi"],
            "traceable": "Sebagian (flag entry/exit)",
            "fincrime_capability": "Flag wallet yang interact dengan mixer (OFAC)",
            "color": "#f59e0b",
        },
        {
            "tier": 3, "label": "Privacy Coin",
            "coins": ["Monero", "Zcash", "Dash", "Pirate"],
            "traceable": "TIDAK (internal) — monitor on/off-ramp",
            "fincrime_capability": "Flag konversi via exchange + Bappebti non-approved",
            "color": "#ef4444",
        },
    ]

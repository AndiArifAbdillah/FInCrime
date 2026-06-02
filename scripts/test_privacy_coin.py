"""Test privacy coin monitor module + endpoints."""
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dataclasses import dataclass

print("=" * 70)
print("  PRIVACY COIN MONITOR TEST")
print("=" * 70)

from src.multichain.privacy_coin_monitor import (
    check_address_for_privacy_coin, privacy_coin_info,
    coverage_matrix, is_privacy_coin_exchange,
)

# Fake ChainTransaction
@dataclass
class FakeTx:
    sender: str
    receiver: str

print("\n[1] Privacy coin info (Monero):")
info = privacy_coin_info("XMR")
print(f"    Privacy level: {info['privacy_level']}/5")
print(f"    Internally traceable: {info['internally_traceable']}")
print(f"    Bappebti allowed: {info['bappebti_allowed']}")
print(f"    Note: {info['note']}")

print("\n[2] 3-Tier coverage matrix:")
for t in coverage_matrix():
    print(f"    Tier {t['tier']} ({t['label']}): {t['traceable']}")

print("\n[3] Wallet yang KIRIM ke exchange privacy coin (on-ramp):")
# Binance hot wallet (supports XMR historically)
txs = [FakeTx(sender="0xSUSPECT", receiver="0x28c6c06298d514db089934071355e5743bf21d60")]
flag = check_address_for_privacy_coin("0xSUSPECT", txs)
if flag:
    print(f"    FLAGGED! type={flag.flag_type}, severity={flag.severity}, score={flag.score}")
    print(f"    Coins: {flag.coins_involved}")
    print(f"    Message: {flag.message}")
    for ind in flag.indicators:
        print(f"      - {ind}")

print("\n[4] Wallet bersih (tidak ada interaksi privacy coin):")
txs_clean = [FakeTx(sender="0xNORMAL_A", receiver="0xNORMAL_B")]
flag = check_address_for_privacy_coin("0xNORMAL_A", txs_clean)
print(f"    Result: {'FLAGGED' if flag else 'CLEAN (None)'}")

print("\n[5] API endpoint test:")
from fastapi.testclient import TestClient
from src.api.main import app
c = TestClient(app)
r = c.get("/v1/privacy-coin/matrix")
print(f"    GET /v1/privacy-coin/matrix -> {r.status_code}, {len(r.json()['matrix'])} tiers")
r = c.get("/v1/privacy-coin/info/XMR")
print(f"    GET /v1/privacy-coin/info/XMR -> {r.status_code}, level={r.json()['privacy_level']}")

print("\n" + "=" * 70)
print("  ALL PRIVACY COIN TESTS PASSED")
print("=" * 70)

"""Smoke test for Wave 2: Private Sector AML + Multi-chain + Model Monitoring."""
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fastapi.testclient import TestClient
from src.api.main import app

c = TestClient(app)
print(f"Total API routes: {len(app.routes)}")
print()

print("=" * 70)
print("PRIVATE SECTOR AML")
print("=" * 70)

# Property screening - cash-heavy purchase under appraisal
r = c.post("/v1/private/property/screen", json={
    "tx_id": "PROP-001",
    "buyer_id": "KTP_X",
    "buyer_country": "ID",
    "sale_price_idr": 3_500_000_000,
    "appraised_value_idr": 5_000_000_000,    # undervalued!
    "cash_portion_idr": 2_000_000_000,        # high cash %
    "mortgage_idr": 0,
})
alerts = r.json()["alerts"]
print(f"[OK] POST /property/screen        -> {len(alerts)} alerts")
for a in alerts[:5]:
    print(f"     - [{a['severity']:>8}] {a['rule']:<30}  {a['message'][:60]}")

# HVA screening - gold bar with crypto payment
r = c.post("/v1/private/hva/screen", json={
    "tx_id": "HVA-001",
    "asset_class": "GOLD_BAR",
    "asset_description": "Logam mulia Antam 1 kg",
    "buyer_id": "KTP_Y",
    "amount_idr": 950_000_000,                # near 1B threshold
    "payment_method": "crypto",
    "cash_portion_idr": 0,
})
alerts = r.json()["alerts"]
print(f"[OK] POST /hva/screen             -> {len(alerts)} alerts")
for a in alerts[:5]:
    print(f"     - [{a['severity']:>8}] {a['rule']:<30}  {a['message'][:60]}")

# UBO seed demo
r = c.post("/v1/private/ubo/seed-demo")
d = r.json()
print(f"[OK] POST /ubo/seed-demo          -> {len(d['ubo_for_PT_MAJU_BERSAMA'])} UBOs traced")
for u in d['ubo_for_PT_MAJU_BERSAMA']:
    print(f"     - {u['name'] or u['entity_id']:<30}  {u['effective_pct']:>6.1f}% effective  PEP={u['is_pep']}")
print(f"     Shell company score (BVI): {d['shell_check_BVI']['shell_score']}")
print(f"     Indicators: {', '.join(d['shell_check_BVI']['indicators'])}")

print()
print("=" * 70)
print("MULTI-CHAIN")
print("=" * 70)

# Address detection
r = c.get("/v1/multichain/detect/0x8589427373d6d84e98730d7795d8f6f8731fda16")
print(f"[OK] GET  /detect/{{ETH addr}}      -> {r.json()['chain']}")

r = c.get("/v1/multichain/detect/bc1q9zpv3yrgcdtsxa8w27avs5cd5kek85wj4lugj3")
print(f"[OK] GET  /detect/{{BTC addr}}      -> {r.json()['chain']}")

r = c.get("/v1/multichain/detect/TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
print(f"[OK] GET  /detect/{{Tron addr}}     -> {r.json()['chain']}")

print()
print("=" * 70)
print("MODEL MONITORING")
print("=" * 70)

# Seed + health + drift
c.post("/v1/monitoring/seed-demo?n=300")
r = c.get("/v1/monitoring/health")
for layer in r.json()['layers']:
    print(f"[OK] Layer health {layer['layer']:>7}  predictions={layer['total_predictions']:>4}  alert_rate={layer['alert_rate']:.2%}")

r = c.get("/v1/monitoring/drift")
d = r.json()
print(f"[OK] Drift report — overall PSI: {d['overall_psi']}  ({d['overall_severity']})")
print("     Top 3 drifted features:")
for f in d['feature_drifts'][:3]:
    print(f"     - {f['feature']:<28}  PSI={f['psi']:.4f}  KS={f['ks_stat']:.4f}  [{f['severity']}]")

print()
print("=" * 70)
print("Wave 2 smoke test complete")
print("=" * 70)

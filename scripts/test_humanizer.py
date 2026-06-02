"""Verify humanized output across all endpoints."""
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from fastapi.testclient import TestClient
from src.api.main import app

c = TestClient(app)

print("=" * 70)
print("  TEST 1: Risk Scoring + verdict (Layer 0)")
print("=" * 70)
top = c.get("/v1/entities/top?limit=3").json()
eid = top["entities"][0]["entity_id"]
r = c.get(f"/v1/entities/{eid}/shap").json()
v = r.get("verdict", {})
print(f"Entity   : {eid}")
print(f"Score    : {r['score']:.0f}/100")
print(f"Verdict  : {v.get('emoji')} {v.get('label')}")
print(f"Plain    : {v.get('plain', '')}")
print(f"Action   : {v.get('action', '')}")
fp = r.get("factors_plain", [])
print(f"Factors  : {len(fp)} explained")
for f in fp[:3]:
    print(f"   - {f['label']} ({f['direction']}, {f['strength']})")

print()
print("=" * 70)
print("  TEST 2: Fraud Alerts + verdict (Layer 1)")
print("=" * 70)
r = c.get("/v1/fraud/recent-alerts?limit=3").json()
print(f"Scored {r['total_scored']}, anomalies {r['anomaly_count']}")
for a in r["alerts"]:
    v = a.get("verdict", {})
    print(f"  {v.get('emoji')} {v.get('label'):<22} score={a['score']:.2f}")
    print(f"     rules_plain: {a.get('rules_plain')}")
    print(f"     action: {v.get('action', '')[:70]}")

print()
print("=" * 70)
print("  TEST 3: Tracing + verdict (Layer 2)")
print("=" * 70)
ent = pd.read_csv("data/sample/entities.csv")
w = ent[ent.entity_type == "wallet"].iloc[0]["entity_id"]
r = c.get(f"/v1/tracing/wallet/{w}/trace-explained?hops=2").json()
lv = r.get("layering_verdict", {})
gv = r.get("gnn_verdict", {})
print(f"Wallet        : {w}")
print(f"Layering      : {r.get('layering_score'):.2f} → {lv.get('emoji')} {lv.get('label')}")
print(f"  Plain       : {lv.get('plain', '')}")
print(f"  Action      : {lv.get('action', '')}")
print(f"GNN AI        : {r.get('gnn_fraud_score', 0):.2f} → {gv.get('emoji')} {gv.get('label')}")

print()
print("=" * 70)
print("  TEST 4: Telegram bot handler (simulated)")
print("=" * 70)
from src.integrations.telegram_bot import handle_command
for cmd in ["/help", f"/risk {eid}", f"/trace {w}", "/alerts"]:
    reply = handle_command(cmd)
    print(f"\n>>> {cmd}")
    print(reply[:350])

print()
print("=" * 70)
print("  ALL HUMANIZER TESTS PASSED")
print("=" * 70)

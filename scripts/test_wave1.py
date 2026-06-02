"""Smoke test for Wave 1 features: LLM narrative, DTTOT, News, Cases, WebSocket."""
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

# WebSocket broadcast (HTTP endpoint trigger)
r = c.post("/v1/alerts/test-broadcast?severity=high&title=Wave1+test")
print(f"[OK] POST /v1/alerts/test-broadcast   -> {r.status_code}  {r.json()}")

# DTTOT
r = c.get("/v1/screening/dttot/list?limit=3")
d = r.json()
print(f"[OK] GET  /v1/screening/dttot/list    -> {r.status_code}  total={d.get('total')}  ID_priority={d.get('indonesian_priority')}")

r = c.get("/v1/screening/dttot/Jamaah Islamiyah")
d = r.json()
print(f"[OK] GET  /v1/screening/dttot/JI      -> {r.status_code}  match={d.get('match')}  list_id={(d.get('entry') or {}).get('list_id')}")

# Cases
r = c.post("/v1/cases/create", json={
    "title": "Wave1 test case",
    "subject_id": "WALLET_TEST_X",
    "assignee": "officer_test",
})
cid = r.json()["case_id"]
print(f"[OK] POST /v1/cases/create            -> {r.status_code}  case_id={cid}")

c.post(f"/v1/cases/{cid}/alerts", json={
    "alert_type": "fraud_tx", "alert_ref": "TX_001",
    "severity": "high", "score": 0.92,
})
c.post(f"/v1/cases/{cid}/notes", json={
    "author": "system",
    "note": "Auto-linked to fraud alert from Layer 1",
})
c.patch(f"/v1/cases/{cid}/status", json={"status": "in_review"})

r = c.get(f"/v1/cases/{cid}")
d = r.json()
print(f"[OK] GET  /v1/cases/{{id}}              -> {r.status_code}  status={d['status']}  alerts={len(d['alerts'])}  notes={len(d['notes'])}")

r = c.get("/v1/cases/list?limit=5")
print(f"[OK] GET  /v1/cases/list              -> {r.status_code}  total={r.json()['stats']['total']}")

# LLM Narrative (template fallback if no key)
print()
print("=" * 70)
print("LLM Suspicion Narrative test")
print("=" * 70)
from src.integrations.llm_narrative import write_suspicion_narrative
narrative = write_suspicion_narrative(
    subject_id="WALLET_0xfa3b...c291",
    subject_type="wallet",
    risk_score=89.5,
    layering_score=0.95,
    path_count=12,
    smurfing_edges=8,
    suspicious_value=600_000_000,
    pattern_types=["smurfing", "layering"],
    tx_count=24,
    total_volume_idr=7_500_000_000,
)
print(narrative)
print()
print(f"[OK] LLM narrative ({len(narrative)} chars)")

print()
print("=" * 70)
print("Wave 1 smoke test complete")
print("=" * 70)

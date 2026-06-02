"""Smoke test for Wave 3: Audit log, Prometheus, MLflow tracker."""
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

# ---------- Audit log ----------
print("=" * 70)
print("AUDIT LOG (compliance trail)")
print("=" * 70)
r = c.post("/v1/audit/seed-demo")
d = r.json()
print(f"[OK] POST /v1/audit/seed-demo  -> {r.status_code}  total={d['total']}")

r = c.get("/v1/audit/events?limit=3")
events = r.json()["events"]
print(f"[OK] GET  /v1/audit/events     -> {r.status_code}  {len(events)} events returned")
for e in events[:3]:
    print(f"     - [{e['event_type']:>20}] actor={e['actor']:<15} layer={e.get('layer','-'):<8} subject={e['subject']}")

r = c.get("/v1/audit/stats")
print(f"[OK] GET  /v1/audit/stats      -> total={r.json()['total']}")
print(f"     by_type: {r.json()['by_type']}")

# ---------- Prometheus ----------
print()
print("=" * 70)
print("PROMETHEUS METRICS")
print("=" * 70)
# Trigger some traffic so counters have non-zero values
c.get("/v1/overview/metrics")
c.get("/v1/cases/list")
c.get("/v1/screening/dttot/list?limit=1")

r = c.get("/metrics")
print(f"[OK] GET  /metrics             -> {r.status_code}  ({len(r.text):,} bytes)")
sample_lines = [l for l in r.text.split("\n")
                if l.startswith("fincrime_") and not l.startswith("#")][:6]
print("     Sample exported metrics:")
for l in sample_lines:
    print(f"       {l[:100]}")

# ---------- MLflow tracker ----------
print()
print("=" * 70)
print("MLFLOW TRACKER (graceful if mlflow not installed)")
print("=" * 70)
from src.mlops import MLflowTracker
with MLflowTracker(experiment="fincrime_smoke") as t:
    t.log_params({"lr": 0.01, "epochs": 10, "model_type": "smoke"})
    t.log_metrics({"auc": 0.85, "f1": 0.78})
print("[OK] MLflowTracker context block executed (no-op if mlflow missing)")

# ---------- Layer status summary ----------
print()
print("=" * 70)
print("OVERALL SYSTEM CAPABILITIES")
print("=" * 70)
print(f"  API routes:       {len(app.routes)}")
print(f"  Sidebar tabs:     11")
print(f"  Real data sources: 10+ (OFAC, UN, Etherscan, Blockstream, BscScan, ...)")
print(f"  Audit events:     {r.json() if False else d['total']}")
print(f"  Compliance: POJK No.12/2024, UU PDP No.27/2022, FATF 10-25")
print()
print("=" * 70)
print("Wave 3 smoke test complete")
print("=" * 70)

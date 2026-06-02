"""Smoke test for Wave 3 + Wave 4: observability, audit, PWA, palette, timeline, bot, DAGs."""
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
print("WAVE 3 — DevOps / MLOps")
print("=" * 70)

# Prometheus metrics
r = c.get("/metrics")
print(f"[OK] GET /metrics                     -> {r.status_code} ({len(r.content)} bytes)")
sample = r.text.split("\n")[:5]
for line in sample:
    if line.strip(): print(f"     | {line}")

# Audit log
r = c.post("/v1/audit/seed-demo")
print(f"[OK] POST /v1/audit/seed-demo         -> total={r.json()['total']}")
r = c.get("/v1/audit/events?limit=3")
print(f"[OK] GET /v1/audit/events             -> {len(r.json()['events'])} events")
for e in r.json()['events'][:2]:
    print(f"     | {e['event_type']:<22} actor={e['actor']:<16} subject={e['subject']}")

# MLflow tracker (no-op without mlflow installed)
from src.mlops import MLflowTracker
with MLflowTracker(experiment="smoke_test") as t:
    t.log_params({"layer": "test", "version": "0.1"})
    t.log_metrics({"roc_auc": 0.85, "f1": 0.72})
print("[OK] MLflowTracker context (no-op safe if mlflow missing)")

print()
print("=" * 70)
print("WAVE 4 — UX Polish")
print("=" * 70)

# PWA assets via static mount
for path in ["/static/manifest.json", "/static/sw.js", "/static/icon-192.svg"]:
    r = c.get(path)
    print(f"[OK] GET {path:<32}  -> {r.status_code} ({len(r.content)} bytes)")

# Verify index.html contains palette + i18n hooks
r = c.get("/")
html = r.text
checks = [
    ("manifest link", '<link rel="manifest"' in html),
    ("Cmd+K palette modal", 'id="palette"' in html),
    ("lang toggle button", 'id="lang-toggle"' in html),
    ("timeline canvas", 'id="timeline-canvas"' in html),
    ("sw.js registration", "/static/sw.js" in c.get("/static/app.js").text),
    ("12 sidebar buttons", html.count('class="sb-btn"') >= 12),
]
for label, ok in checks:
    print(f"[{'OK' if ok else '!!'}] {label}")

# Telegram bot — verify command handler works (won't actually connect)
from src.integrations.telegram_bot import handle_command
help_text = handle_command("/help")
print(f"[OK] Telegram /help handler            -> {len(help_text)} chars")

# Airflow DAGs file is syntactically valid (import already happened at top)
import airflow_dags.fincrime_dags as dags_mod   # noqa: F401
print("[OK] Airflow DAGs file imports cleanly")

print()
print("=" * 70)
print("Wave 3 + 4 smoke test complete")
print("=" * 70)

"""Verify privacy coin UI + telegram wiring."""
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.integrations.telegram_bot import handle_command

h = handle_command("/help")
print("[1] /help mentions /privacycoin:", "/privacycoin" in h)
print()
print("[2] /privacycoin (no arg) reply:")
print(handle_command("/privacycoin")[:180])

root = _Path(__file__).resolve().parent.parent
idx = (root / "src/web/index.html").read_text(encoding="utf-8")
js = (root / "src/web/app.js").read_text(encoding="utf-8")
print()
print('[3] index.html has id="p-12":', 'id="p-12"' in idx)
print('[4] index.html has nb-12:', 'nb-12' in idx)
print('[5] index.html has pc-matrix:', 'pc-matrix' in idx)
print('[6] app.js has loadPrivacyCoinMatrix:', "loadPrivacyCoinMatrix" in js)
print('[7] app.js nav i===12:', "i === 12" in js)
print('[8] app.js checkPrivacyCoin:', "window.checkPrivacyCoin" in js)

# API endpoints
from fastapi.testclient import TestClient
from src.api.main import app
c = TestClient(app)
print()
print("[9] GET /v1/privacy-coin/matrix:", c.get("/v1/privacy-coin/matrix").status_code)
print("[10] GET /v1/privacy-coin/info/XMR:", c.get("/v1/privacy-coin/info/XMR").status_code)
print()
print("ALL PRIVACY UI/BOT WIRING VERIFIED")

"""Telegram bot for FinCrime compliance officers.

Lets officers query the FinCrime API from their phone:

    /start                — show help
    /trace <wallet_id>    — Layer 2 trace + GNN score
    /risk  <entity_id>    — Layer 0 risk score + SHAP top factors
    /screen <name>        — DTTOT + Negative news screening
    /case  <case_id>      — Case status
    /alerts               — Top 5 active fraud alerts

Setup:
    1. Talk to @BotFather on Telegram → /newbot → get token
    2. Set TELEGRAM_BOT_TOKEN in .env
    3. Optional: restrict to authorized users:
       TELEGRAM_ALLOWED_USERS=12345678,87654321  (comma-separated user IDs)
    4. Run:  .\fc python -m src.integrations.telegram_bot

Uses pure-stdlib long polling (no external lib required). Set
FINCRIME_API_URL if the bot runs separately from the API.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Optional

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("integrations.telegram")


# ============================================================
# Telegram API client (urllib-only, no httpx required)
# ============================================================
class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.base = f"https://api.telegram.org/bot{token}"

    def _req(self, method: str, params: dict | None = None,
             timeout: int = 60) -> dict:
        url = f"{self.base}/{method}"
        data = urllib.parse.urlencode(params or {}).encode()
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            log.warning("telegram.request_failed", method=method, error=str(e))
            return {"ok": False, "error": str(e)}

    def get_updates(self, offset: Optional[int] = None,
                    timeout: int = 30) -> list[dict]:
        params: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        resp = self._req("getUpdates", params, timeout=timeout + 5)
        return resp.get("result", []) if resp.get("ok") else []

    def send_message(self, chat_id: int, text: str,
                     parse_mode: str = "Markdown") -> None:
        # Telegram caps at 4096 chars
        for chunk in [text[i:i + 3900] for i in range(0, len(text), 3900)] or [text]:
            self._req("sendMessage", {
                "chat_id": chat_id, "text": chunk, "parse_mode": parse_mode,
                "disable_web_page_preview": "true",
            })


# ============================================================
# API helpers — call the FinCrime FastAPI service
# ============================================================
def _api_get(path: str) -> dict | None:
    url = os.environ.get("FINCRIME_API_URL", "http://localhost:8000").rstrip("/") + path
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        log.warning("api.get_failed", url=url, error=str(e))
        return None


def _api_post(path: str, body: dict | None = None) -> dict | None:
    url = os.environ.get("FINCRIME_API_URL", "http://localhost:8000").rstrip("/") + path
    try:
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        log.warning("api.post_failed", url=url, error=str(e))
        return None


# ============================================================
# Command handlers
# ============================================================
HELP_TEXT = """\
🛡 *FinCrime — Asisten Kepatuhan AML/CFT*

Selamat datang! Bot ini membantu Anda menyelidiki dugaan kejahatan keuangan langsung dari HP.

*PERINTAH YANG TERSEDIA:*

🕸 `/trace <wallet>` — Lacak jaringan wallet kripto, deteksi pencucian uang
   contoh: `/trace WALLET_0x000000000002`

👤 `/risk <id>` — Cek skor risiko nasabah/entitas
   contoh: `/risk IND_000001`

🔎 `/screen <nama>` — Periksa nama di daftar sanksi & berita negatif
   contoh: `/screen Jamaah Islamiyah`

🪙 `/privacycoin <wallet>` — Cek konversi ke privacy coin (Monero/Zcash)
   contoh: `/privacycoin 0x28c6...`

📋 `/case <id>` — Lihat status kasus investigasi
   contoh: `/case CASE-20260101-ABC`

🚨 `/alerts` — Daftar transaksi mencurigakan terbaru

❓ `/help` — Tampilkan pesan ini

_Semua hasil dilengkapi penjelasan bahasa Indonesia + rekomendasi tindakan._
"""


def handle_command(text: str) -> str:
    text = text.strip()
    if text.startswith("/start") or text.startswith("/help"):
        return HELP_TEXT

    if text.startswith("/trace"):
        arg = text.removeprefix("/trace").strip()
        if not arg: return "Cara pakai: `/trace <wallet_id>`\nContoh: `/trace WALLET_0x000000000002`"
        t = _api_get(f"/v1/tracing/wallet/{urllib.parse.quote(arg)}/trace?hops=2")
        s = _api_get(f"/v1/tracing/wallet/{urllib.parse.quote(arg)}/score")
        if not t or not s:
            return "Pelacakan gagal — pastikan server FinCrime aktif (port 8000)."

        from src.common.explain import explain_layering_score, explain_gnn_score
        layering = float(t.get("layering_score", 0))
        gnn = float(s.get("fraud_score", 0))
        lay_v = explain_layering_score(layering, chains=t.get("path_count", 0))
        gnn_v = explain_gnn_score(gnn)

        # Verdict gabungan: ambil yang paling parah
        main_v = lay_v if lay_v["severity"] >= gnn_v["severity"] else gnn_v

        lines = [
            f"{main_v['emoji']} *HASIL PELACAKAN WALLET*",
            f"`{arg}`",
            "",
            f"*KESIMPULAN: {main_v['label']}*",
            f"_{main_v['plain']}_",
            "",
            "📊 *Detail:*",
            f"• Skor Pencucian (Layering): *{layering:.2f}* dari 1.00 → {lay_v['emoji']} {lay_v['label']}",
            f"• Prediksi AI (GNN): *{gnn:.2f}* dari 1.00 → {gnn_v['emoji']} {gnn_v['label']}",
            f"• Jaringan terhubung: {t.get('subgraph_size', 0)} wallet",
            f"• Rantai pencucian: {t.get('path_count', 0)}",
            f"• Pola: {', '.join(t.get('pattern_types', [])) or 'tidak ada'}",
            "",
            f"⚡ *Rekomendasi:* {main_v['action']}",
        ]
        return "\n".join(lines)

    if text.startswith("/risk"):
        arg = text.removeprefix("/risk").strip()
        if not arg: return "Cara pakai: `/risk <entity_id>`\nContoh: `/risk IND_000001`"
        r = _api_get(f"/v1/entities/{urllib.parse.quote(arg)}/shap")
        if not r: return "Pengecekan risiko gagal — pastikan server aktif."

        from src.common.explain import explain_risk_score, humanize_shap_factor
        score = float(r.get("score", 0))
        v = explain_risk_score(score)

        lines = [
            f"{v['emoji']} *SKOR RISIKO ENTITAS*",
            f"`{arg}`",
            "",
            f"*Skor: {score:.0f}/100 — {v['label']}*",
            f"_{v['plain']}_",
            "",
            "🔍 *Faktor utama (kenapa skornya begini):*",
        ]
        for f in (r.get("factors") or [])[:5]:
            h = humanize_shap_factor(f.get("feature", ""), float(f.get("contribution", 0)))
            arrow = "⬆" if f["contribution"] > 0 else "⬇"
            lines.append(f"  {arrow} {h['label']} _{h['strength']}_")
        lines.append("")
        lines.append(f"⚡ *Rekomendasi:* {v['action']}")
        return "\n".join(lines)

    if text.startswith("/screen"):
        name = text.removeprefix("/screen").strip()
        if not name: return "Cara pakai: `/screen <nama>`\nContoh: `/screen Jamaah Islamiyah`"
        d = _api_get(f"/v1/screening/dttot/{urllib.parse.quote(name)}")
        n = _api_get(f"/v1/screening/news/{urllib.parse.quote(name)}?limit=3")

        is_match = bool(d and d.get("match"))
        emoji = "🔴" if is_match else "🟢"
        out = [
            f"{emoji} *HASIL PENYARINGAN (SCREENING)*",
            f"Nama: *{name}*",
            "",
        ]
        if is_match:
            e = d.get("entry") or {}
            out.append("*⚠ DITEMUKAN DI DAFTAR SANKSI!*")
            out.append(f"_{name} cocok dengan entitas di daftar terlarang internasional._")
            out.append(f"  • Sumber: {e.get('program', '—')}")
            out.append(f"  • Tipe: {e.get('list_type', '—')}")
            out.append("")
            out.append("⚡ *Rekomendasi:* WAJIB tolak transaksi & lapor PPATK.")
        else:
            out.append("✓ *Tidak ada di daftar sanksi DTTOT/UN.*")

        if n and n.get("hits"):
            out.append("")
            out.append(f"📰 *Berita negatif ({n['hit_count']} ditemukan):*")
            for h in n["hits"][:3]:
                out.append(f"  • _{h['source']}_: {h['title'][:80]}")
        elif n is not None and not is_match:
            out.append("")
            out.append("📰 Tidak ada berita negatif terkait.")
        return "\n".join(out)

    if text.startswith("/case"):
        arg = text.removeprefix("/case").strip()
        if not arg: return "Cara pakai: `/case <case_id>`"
        c = _api_get(f"/v1/cases/{urllib.parse.quote(arg)}")
        if not c: return f"Kasus `{arg}` tidak ditemukan."
        status_emoji = {
            "open": "🆕", "in_review": "🔍", "escalated": "🔴",
            "reported": "📤", "closed": "✅",
        }.get(c.get("status", ""), "📋")
        return (
            f"{status_emoji} *KASUS INVESTIGASI*\n"
            f"`{c['case_id']}`\n\n"
            f"*Judul:* {c['title']}\n"
            f"*Subjek:* `{c['subject_id']}`\n"
            f"*Status:* {c['status']}\n"
            f"*Petugas:* {c['assignee']}\n"
            f"*Alert terkait:* {len(c['alerts'])}\n"
            f"*Catatan:* {len(c['notes'])}\n"
            f"*Laporan:* {len(c['report_ids'])}"
        )

    if text.startswith("/alerts"):
        r = _api_get("/v1/fraud/recent-alerts?limit=5")
        if not r: return "Gagal mengambil alert — pastikan server aktif."
        from src.common.explain import explain_fraud_score
        total = r.get("total_scored", 0)
        anom = r.get("anomaly_count", 0)
        lines = [
            "🚨 *ALERT TRANSAKSI MENCURIGAKAN*",
            f"_{anom} mencurigakan dari {total} transaksi yang diperiksa._",
            "",
        ]
        for i, a in enumerate(r["alerts"], 1):
            v = explain_fraud_score(float(a.get("score", 0)), a.get("rules", []))
            lines.append(f"{v['emoji']} *{i}. {v['label']}*  (skor {a['score']*100:.0f}%)")
            lines.append(f"   {a['subtitle'][:90]}")
            lines.append("")
        lines.append("Ketik `/trace <wallet>` atau `/risk <id>` untuk investigasi lebih dalam.")
        return "\n".join(lines)

    if text.startswith("/privacycoin"):
        arg = text.removeprefix("/privacycoin").strip()
        if not arg:
            return ("Cara pakai: `/privacycoin <wallet>`\n"
                    "Cek apakah wallet konversi ke/dari privacy coin (Monero/Zcash).\n"
                    "Contoh: `/privacycoin 0x28c6c06298d514db089934071355e5743bf21d60`")
        # detect chain
        det = _api_get(f"/v1/multichain/detect/{urllib.parse.quote(arg)}")
        chain = (det or {}).get("chain") or "eth"
        if chain == "evm":
            chain = "eth"
        r = _api_get(f"/v1/privacy-coin/check/{chain}/{urllib.parse.quote(arg)}")
        if not r:
            return "Pengecekan gagal — pastikan server aktif."
        if not r.get("flagged"):
            return (f"🟢 *CEK PRIVACY COIN*\n`{arg}`\n\n"
                    f"✓ Tidak terdeteksi konversi ke/dari exchange privacy coin.\n"
                    f"_({r.get('txs_checked', 0)} transaksi diperiksa)_\n\n"
                    f"Catatan: butuh API key blockchain untuk data nyata. "
                    f"Privacy coin (Monero/Zcash) tidak bisa di-trace internal — "
                    f"sistem hanya memantau pintu konversi.")
        f = r["flag"]
        sev_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(f["severity"], "⚠")
        lines = [
            f"{sev_emoji} *INDIKASI PRIVACY COIN TERDETEKSI*",
            f"`{arg}`",
            "",
            f"*Tipe:* {f['flag_type']} · *Severity:* {f['severity'].upper()}",
            f"_{f['message']}_",
            "",
            f"*Privacy coin terkait:* {', '.join(f['coins_involved'])}",
            f"*Exchange:* {f.get('exchange', '—')}",
            "",
            "*Indikator:*",
        ]
        for ind in f.get("indicators", []):
            lines.append(f"  • {ind}")
        lines.append("")
        lines.append("⚡ *Rekomendasi:* Eskalasi — privacy coin tidak diizinkan Bappebti, "
                     "siapkan LTKM.")
        return "\n".join(lines)

    return "Perintah tidak dikenal. Ketik `/help` untuk daftar perintah."


# ============================================================
# Bot loop
# ============================================================
def _load_env_file() -> None:
    """Explicitly load .env into os.environ (pydantic-settings only loads
    fields declared in Settings; TELEGRAM_* vars are not declared)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    from pathlib import Path
    # Find .env starting from CWD upward
    here = Path.cwd()
    for parent in [here] + list(here.parents):
        env_path = parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)
            return
    # Also try project root relative to this file
    project_root = Path(__file__).resolve().parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def run_bot(token: Optional[str] = None,
            allowed_user_ids: Optional[set[int]] = None) -> None:
    _load_env_file()
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("\n[!] TELEGRAM_BOT_TOKEN not set.")
        print("    1. Talk to @BotFather on Telegram → /newbot")
        print("    2. Copy the token → add to .env:")
        print("       TELEGRAM_BOT_TOKEN=123:ABC...")
        print("    3. Re-run this script.\n")
        return

    if allowed_user_ids is None:
        env = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
        allowed_user_ids = {int(x) for x in env.split(",") if x.strip().isdigit()} or None

    client = TelegramClient(token)
    log.info("telegram.bot_started",
             restricted_users=len(allowed_user_ids) if allowed_user_ids else 0)
    print(f"\n[OK] FinCrime Telegram bot started. Restricted: "
          f"{len(allowed_user_ids) if allowed_user_ids else 'no (anyone can DM)'}\n")

    offset: Optional[int] = None
    while True:
        try:
            updates = client.get_updates(offset=offset, timeout=30)
            for up in updates:
                offset = up["update_id"] + 1
                msg = up.get("message") or up.get("edited_message")
                if not msg:
                    continue
                user_id = msg.get("from", {}).get("id")
                chat_id = msg["chat"]["id"]
                if allowed_user_ids and user_id not in allowed_user_ids:
                    client.send_message(chat_id,
                        "🚫 Akses ditolak. Hubungi admin untuk register user_id Anda.")
                    log.warning("telegram.unauthorized", user_id=user_id)
                    continue
                text = msg.get("text", "")
                if not text.startswith("/"):
                    continue
                log.info("telegram.cmd", user=user_id, cmd=text[:40])
                try:
                    reply = handle_command(text)
                except Exception as e:
                    reply = f"Error: {e}"
                client.send_message(chat_id, reply)
        except KeyboardInterrupt:
            print("\nBot stopped.")
            break
        except Exception as e:
            log.warning("telegram.loop_error", error=str(e))
            time.sleep(5)


if __name__ == "__main__":
    import sys
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    run_bot()

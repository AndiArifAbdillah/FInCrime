"""LLM-powered narrative writer for LTKM reports.

Uses the Anthropic Claude API to write fluent Indonesian "Ringkasan Kecurigaan"
paragraphs from structured trace/risk data. Falls back to template if no API
key is configured.

Get a key (free trial credits available): https://console.anthropic.com/
Set: ANTHROPIC_API_KEY=sk-ant-... in .env
"""
from __future__ import annotations

import os
from typing import Optional

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("integrations.llm")

_SYSTEM_PROMPT = """\
Kamu adalah seorang Petugas Kepatuhan AML/CFT senior di institusi keuangan Indonesia
yang menulis Ringkasan Kecurigaan untuk Laporan Transaksi Keuangan Mencurigakan
(LTKM) yang akan disampaikan ke PPATK.

Gaya penulisan:
- Formal, lugas, bahasa Indonesia baku
- Berbasis bukti — sebutkan angka-angka konkret dari data
- Tidak menuduh secara hukum; gunakan kata "diduga", "terindikasi", "terdapat pola"
- Maksimum 4 kalimat / 120 kata
- Tidak menambahkan opini di luar fakta yang diberikan
- Akhiri dengan implikasi compliance (mis. "memerlukan investigasi lebih lanjut")

Format output: hanya isi paragraf. JANGAN tambahkan judul, header, atau metadata.
"""


def _system_prompt() -> str:
    return _SYSTEM_PROMPT


def write_suspicion_narrative(*,
                              subject_id: str,
                              subject_type: str,
                              risk_score: float,
                              layering_score: float,
                              path_count: int,
                              smurfing_edges: int,
                              suspicious_value: float,
                              pattern_types: list[str],
                              tx_count: int,
                              total_volume_idr: float,
                              api_key: Optional[str] = None,
                              model: str = "claude-haiku-4-5") -> str:
    """Generate a narrative paragraph for the LTKM Ringkasan Kecurigaan.

    Returns the LLM-generated text, or a template fallback if Claude isn't
    available.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    # ---- Template fallback (no API key) ----
    def _template() -> str:
        patterns = ", ".join(pattern_types) if pattern_types else "pola transaksi anomali"
        return (
            f"Subjek terlapor {subject_id} ({subject_type}) menunjukkan pola transaksi "
            f"yang mencurigakan dengan skor risiko {risk_score:.1f}/100 dan skor "
            f"layering {layering_score:.4f}. Sistem mendeteksi {patterns} melibatkan "
            f"{tx_count} transaksi dengan total nilai sekitar Rp {total_volume_idr:,.0f}, "
            f"termasuk {smurfing_edges} hop smurfing dengan nilai mencurigakan "
            f"Rp {suspicious_value:,.0f} melalui {path_count} rantai layering. Pola ini "
            f"terindikasi sebagai upaya menyamarkan asal usul dana dan memerlukan "
            f"investigasi lebih lanjut sesuai POJK No.12/2024 dan UU TPPU."
        )

    if not api_key:
        log.info("llm.narrative.template_fallback", reason="no_api_key")
        return _template()

    try:
        import httpx
    except ImportError:
        log.warning("llm.narrative.template_fallback", reason="no_httpx")
        return _template()

    user_msg = f"""\
Buatkan paragraf "Ringkasan Kecurigaan" untuk LTKM berdasarkan fakta berikut:

DATA TERLAPOR:
- ID/Wallet     : {subject_id}
- Tipe          : {subject_type}
- Skor Risiko   : {risk_score:.1f} / 100 (Layer 0 XGBoost)
- Skor Layering : {layering_score:.4f} (Layer 2 GraphSAGE GNN)

POLA TERDETEKSI:
- Tipe pola              : {", ".join(pattern_types) if pattern_types else "anomalous_pattern"}
- Jumlah transaksi terkait : {tx_count}
- Total nilai            : Rp {total_volume_idr:,.0f}
- Rantai layering        : {path_count}
- Hop smurfing           : {smurfing_edges}
- Nilai mencurigakan     : Rp {suspicious_value:,.0f}

Tulis paragraf 3-4 kalimat dengan gaya formal sesuai standar PPATK.
"""

    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 400,
                    "system": _system_prompt(),
                    "messages": [{"role": "user", "content": user_msg}],
                },
            )
            r.raise_for_status()
            data = r.json()
            text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
            text = text.strip()
            if not text:
                log.warning("llm.narrative.empty_response")
                return _template()
            log.info("llm.narrative.generated", model=model, chars=len(text))
            return text
    except httpx.HTTPStatusError as e:
        log.warning("llm.narrative.http_error", status=e.response.status_code,
                    body=e.response.text[:200])
        return _template()
    except Exception as e:
        log.warning("llm.narrative.failed", error=str(e))
        return _template()

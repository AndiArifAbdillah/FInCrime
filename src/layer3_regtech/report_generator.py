"""Generate LTKM (Suspicious) and LTKT (Cash Transaction ≥ IDR 500M) reports for PPATK."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.common.config import settings
from src.common.logger import get_logger
from src.common.utils import make_id, now_iso

log = get_logger("layer3.report")

TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass
class LTKMPayload:
    """Schema modeled after PPATK GRIPS (LTKM) format — simplified for prototype."""
    report_id: str
    institution_code: str
    institution_name: str
    report_date: str                 # ISO date
    subject_name: str                # the reported entity
    subject_id: str
    subject_type: str                # "individual" | "corporate" | "wallet"
    subject_country: str
    transactions: list[dict] = field(default_factory=list)
    suspicion_summary: str = ""
    suspicion_indicators: list[str] = field(default_factory=list)
    layering_score: float = 0.0
    related_wallets: list[str] = field(default_factory=list)
    risk_score: float = 0.0
    officer_name: str = "AUTO-GENERATED"
    officer_id: str = "SYS-AI"


@dataclass
class LTKTPayload:
    """Cash transaction report — IDR 500M+ in a single business day."""
    report_id: str
    institution_code: str
    institution_name: str
    report_date: str
    customer_name: str
    customer_id: str
    customer_type: str
    transactions: list[dict] = field(default_factory=list)
    total_amount: float = 0.0
    transaction_count: int = 0
    officer_name: str = "AUTO-GENERATED"
    officer_id: str = "SYS-AI"


class ReportGenerator:
    """Render LTKM/LTKT to HTML and JSON. PDF requires WeasyPrint (optional)."""

    def __init__(self, template_dir: Path | None = None):
        td = template_dir or TEMPLATE_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(td)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["idr"] = self._idr
        self.env.filters["dt"] = self._dt

    # ----- filters -----
    @staticmethod
    def _idr(value) -> str:
        try:
            return f"Rp {float(value):,.0f}".replace(",", ".")
        except (ValueError, TypeError):
            return str(value)

    @staticmethod
    def _dt(value) -> str:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "")).strftime("%d %B %Y %H:%M:%S")
        except Exception:
            return str(value)

    # ----- renderers -----
    def render_ltkm_html(self, payload: LTKMPayload) -> str:
        tpl = self.env.get_template("ltkm_template.html.j2")
        return tpl.render(p=payload, generated_at=now_iso())

    def render_ltkt_html(self, payload: LTKTPayload) -> str:
        tpl = self.env.get_template("ltkt_template.html.j2")
        return tpl.render(p=payload, generated_at=now_iso())

    def to_json(self, payload: LTKMPayload | LTKTPayload) -> str:
        d = payload.__dict__.copy()
        return json.dumps(d, indent=2, ensure_ascii=False, default=str)

    # ----- write to disk -----
    def write(self, payload: LTKMPayload | LTKTPayload, out_dir: Path) -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        base = out_dir / payload.report_id
        is_ltkm = isinstance(payload, LTKMPayload)
        html_path = base.with_suffix(".html")
        json_path = base.with_suffix(".json")
        if is_ltkm:
            html_path.write_text(self.render_ltkm_html(payload), encoding="utf-8")
        else:
            html_path.write_text(self.render_ltkt_html(payload), encoding="utf-8")
        json_path.write_text(self.to_json(payload), encoding="utf-8")

        result = {"html": str(html_path), "json": str(json_path)}

        # PDF rendering: try WeasyPrint first, then fall back to a headless
        # browser (Edge/Chrome) which needs no GTK system libraries on Windows.
        pdf_path = base.with_suffix(".pdf")
        try:
            from weasyprint import HTML
            HTML(string=html_path.read_text(encoding="utf-8")).write_pdf(str(pdf_path))
            result["pdf"] = str(pdf_path)
        except Exception as e:
            if _html_to_pdf_via_browser(html_path, pdf_path):
                result["pdf"] = str(pdf_path)
                log.info("ltkm.pdf_rendered_via_browser", pdf=str(pdf_path))
            else:
                log.warning("ltkm.pdf_render_failed", error=str(e))

        log.info("report.written", report_id=payload.report_id, **result)
        return result


def _html_to_pdf_via_browser(html_file: Path, pdf_file: Path) -> bool:
    """Render HTML to PDF via headless Edge/Chrome (Windows-friendly, no GTK).

    Returns True if the PDF was produced. Used as a fallback when WeasyPrint is
    unavailable or its native libraries (libgobject/pango/cairo) are missing.
    """
    import os
    import shutil
    import subprocess
    import tempfile

    # Chrome first (its headless print-to-pdf is the most reliable), then Edge.
    candidates = [
        shutil.which("chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    pdf_abs = str(Path(pdf_file).resolve())          # headless needs an absolute path
    url = Path(html_file).resolve().as_uri()
    for browser in candidates:
        if not browser or not os.path.exists(browser):
            continue
        profile = tempfile.mkdtemp(prefix="fc-pdf-")  # isolated profile avoids lock
        try:
            subprocess.run(
                [
                    browser, "--headless=new", "--disable-gpu",
                    f"--user-data-dir={profile}", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_abs}", url,
                ],
                timeout=90,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if os.path.exists(pdf_abs):
                return True
        except Exception:
            pass
        finally:
            shutil.rmtree(profile, ignore_errors=True)
    return False


# ===== Convenience builders =====
def build_ltkm_from_trace(*, subject_id: str, subject_name: str,
                          subject_type: str = "wallet",
                          subject_country: str = "XX",
                          trace_result: dict,
                          risk_score: float = 0.0,
                          transactions: Optional[list[dict]] = None,
                          use_llm: bool = True) -> LTKMPayload:
    indicators: list[str] = []
    if trace_result.get("layering_score", 0) >= 0.5:
        indicators.append("Indikasi pola layering (rangkaian transfer untuk menyamarkan asal usul dana).")
    if trace_result.get("path_count", 0) > 0:
        indicators.append(f"Terdeteksi {trace_result['path_count']} rantai layering pada jaringan.")
    if "smurfing" in str(trace_result.get("pattern_types", "")):
        indicators.append(
            "Pola smurfing terdeteksi: nominal sengaja dipecah kecil (di bawah ambang "
            "deteksi internal Rp 50 juta) untuk menghindari ambang wajib lapor LTKT "
            "Rp 500 juta."
        )
    if risk_score >= settings.risk_score_high:
        indicators.append(f"Skor risiko entitas tinggi ({risk_score:.1f}/100).")

    # ----- LLM-powered narrative (with template fallback) -----
    summary = trace_result.get(
        "explanation",
        "Sistem AI mendeteksi pola transaksi mencurigakan pada entitas terlapor."
    )
    if use_llm:
        try:
            from src.integrations.llm_narrative import write_suspicion_narrative
            tx_list = transactions or []
            total_volume = sum(float(t.get("amount_idr", 0)) for t in tx_list)
            patterns = trace_result.get("pattern_types", [])
            if isinstance(patterns, str):
                patterns = [patterns]
            summary = write_suspicion_narrative(
                subject_id=subject_id,
                subject_type=subject_type,
                risk_score=risk_score,
                layering_score=float(trace_result.get("layering_score", 0)),
                path_count=int(trace_result.get("path_count", 0)),
                smurfing_edges=int(trace_result.get("smurfing_edges", 0)),
                suspicious_value=float(trace_result.get("suspicious_value", 0)),
                pattern_types=[str(p) for p in patterns],
                tx_count=len(tx_list),
                total_volume_idr=total_volume,
            )
        except Exception as e:
            log.warning("ltkm.llm_failed", error=str(e))

    return LTKMPayload(
        report_id=f"LTKM-{datetime.utcnow().strftime('%Y%m%d')}-{make_id('R')[:8]}",
        institution_code=settings.ppatk_institution_code,
        institution_name="FinCrime Demo Bank",
        report_date=datetime.utcnow().strftime("%Y-%m-%d"),
        subject_name=subject_name,
        subject_id=subject_id,
        subject_type=subject_type,
        subject_country=subject_country,
        transactions=transactions or [],
        suspicion_summary=summary,
        suspicion_indicators=indicators,
        layering_score=float(trace_result.get("layering_score", 0.0)),
        related_wallets=list(trace_result.get("flagged_wallets", []))[:50],
        risk_score=float(risk_score),
    )


def build_ltkt_from_transactions(*, customer_id: str, customer_name: str,
                                 customer_type: str,
                                 transactions: list[dict]) -> Optional[LTKTPayload]:
    """Aggregate same-day cash transactions ≥ IDR 500M for the LTKT trigger."""
    THRESHOLD = 500_000_000
    total = sum(float(t.get("amount_idr", 0)) for t in transactions)
    if total < THRESHOLD:
        return None
    return LTKTPayload(
        report_id=f"LTKT-{datetime.utcnow().strftime('%Y%m%d')}-{make_id('R')[:8]}",
        institution_code=settings.ppatk_institution_code,
        institution_name="FinCrime Demo Bank",
        report_date=datetime.utcnow().strftime("%Y-%m-%d"),
        customer_name=customer_name,
        customer_id=customer_id,
        customer_type=customer_type,
        transactions=transactions,
        total_amount=total,
        transaction_count=len(transactions),
    )

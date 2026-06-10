"""Layer 3 — Regtech / PPATK report endpoints."""
from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from src.common.config import settings
from src.layer3_regtech.report_generator import (
    LTKMPayload, build_ltkm_from_trace, build_ltkt_from_transactions,
)
from ..dependencies import get_report_generator, get_crypto_tracer

router = APIRouter()

REPORTS_DIR = settings.app_data_dir / "reports"


class LTKMRequest(BaseModel):
    subject_id: str
    subject_name: str
    subject_type: str = "wallet"
    subject_country: str = "XX"
    transactions: list[dict] = []


class LTKTRequest(BaseModel):
    customer_id: str
    customer_name: str
    customer_type: str = "individual"
    transactions: list[dict]


@router.post("/ltkm/auto/{wallet_id}")
def auto_ltkm_for_wallet(wallet_id: str,
                         subject_name: str | None = None,
                         tracer=Depends(get_crypto_tracer),
                         gen=Depends(get_report_generator)):
    """Auto-build an LTKM from Layer 2 trace results for a suspicious wallet."""
    trace = tracer.trace(wallet_id, hops=2).model_dump()
    payload = build_ltkm_from_trace(
        subject_id=wallet_id,
        subject_name=subject_name or wallet_id,
        subject_type="wallet",
        trace_result=trace,
        risk_score=float(tracer.fraud_score(wallet_id) * 100),
    )
    paths = gen.write(payload, REPORTS_DIR)
    return {"report_id": payload.report_id, "paths": paths, "trace": trace}


@router.post("/ltkm")
def create_ltkm(req: LTKMRequest, gen=Depends(get_report_generator)):
    """Create an LTKM manually from compliance-officer-supplied data."""
    from src.common.utils import make_id, utc_now
    payload = LTKMPayload(
        report_id=f"LTKM-{utc_now().strftime('%Y%m%d')}-{make_id('M')[:8]}",
        institution_code=settings.ppatk_institution_code,
        institution_name="FinCrime Demo Bank",
        report_date=utc_now().strftime("%Y-%m-%d"),
        subject_name=req.subject_name,
        subject_id=req.subject_id,
        subject_type=req.subject_type,
        subject_country=req.subject_country,
        transactions=req.transactions,
        suspicion_summary="Laporan dibuat manual oleh petugas kepatuhan.",
    )
    paths = gen.write(payload, REPORTS_DIR)
    return {"report_id": payload.report_id, "paths": paths}


@router.post("/ltkt")
def create_ltkt(req: LTKTRequest, gen=Depends(get_report_generator)):
    payload = build_ltkt_from_transactions(
        customer_id=req.customer_id,
        customer_name=req.customer_name,
        customer_type=req.customer_type,
        transactions=req.transactions,
    )
    if payload is None:
        raise HTTPException(status_code=400,
                            detail="Total < IDR 500M — LTKT threshold not met.")
    paths = gen.write(payload, REPORTS_DIR)
    return {"report_id": payload.report_id, "paths": paths}


@router.get("/{report_id}/preview", response_class=HTMLResponse)
def preview(report_id: str):
    p = REPORTS_DIR / f"{report_id}.html"
    if not p.exists():
        raise HTTPException(404, "Report not found")
    return HTMLResponse(p.read_text(encoding="utf-8"))


@router.get("/{report_id}/download")
def download(report_id: str, fmt: str = "json"):
    p = REPORTS_DIR / f"{report_id}.{fmt}"
    if not p.exists():
        raise HTTPException(404, f"{fmt} format not found")
    return FileResponse(str(p), filename=p.name)

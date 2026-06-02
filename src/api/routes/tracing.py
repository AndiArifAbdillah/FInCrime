"""Layer 2 — Crypto Tracing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.common.schemas import GraphTraceResult
from ..dependencies import get_crypto_tracer

router = APIRouter()


@router.get("/wallet/{wallet_id}/score")
def wallet_score(wallet_id: str, tracer=Depends(get_crypto_tracer)):
    """Return the GNN-predicted fraud probability for a wallet."""
    try:
        score = tracer.fraud_score(wallet_id)
        from src.common.explain import explain_gnn_score
        return {
            "wallet": wallet_id,
            "fraud_score": score,
            "verdict": explain_gnn_score(float(score)),   # NEW
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/wallet/{wallet_id}/trace", response_model=GraphTraceResult)
def trace_wallet(wallet_id: str,
                 hops: int = Query(2, ge=1, le=4),
                 tracer=Depends(get_crypto_tracer)):
    """Run subgraph + layering detection around a seed wallet."""
    try:
        return tracer.trace(wallet_id, hops=hops)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/wallet/{wallet_id}/trace-explained")
def trace_wallet_explained(wallet_id: str,
                           hops: int = Query(2, ge=1, le=4),
                           tracer=Depends(get_crypto_tracer)):
    """Trace + plain-language verdict (for non-technical users / regulators)."""
    try:
        result = tracer.trace(wallet_id, hops=hops)
        from src.common.explain import explain_layering_score, explain_gnn_score
        gnn = tracer.fraud_score(wallet_id)
        # suspicious value diparse dari explanation kalau ada
        layering_verdict = explain_layering_score(
            float(result.layering_score),
            chains=result.path_count,
        )
        d = result.model_dump()
        d["gnn_fraud_score"] = float(gnn)
        d["layering_verdict"] = layering_verdict       # NEW plain-language
        d["gnn_verdict"] = explain_gnn_score(float(gnn))  # NEW
        return d
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

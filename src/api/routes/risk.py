"""Layer 0 — Risk Scoring endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.common.schemas import Entity, RiskScore
from ..dependencies import get_risk_scorer

router = APIRouter()


@router.post("/score", response_model=RiskScore)
def score_entity(entity: Entity, scorer=Depends(get_risk_scorer)):
    """Score a single entity. Returns risk 0–100 plus top-5 SHAP factors."""
    try:
        return scorer.score_one(entity, with_shap=True)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/score-batch", response_model=list[RiskScore])
def score_batch(entities: list[Entity], scorer=Depends(get_risk_scorer)):
    """Batch scoring (no SHAP for speed). Max 1,000 entities per call."""
    if len(entities) > 1000:
        raise HTTPException(status_code=400, detail="Batch size limit is 1000")
    try:
        return scorer.score_batch(entities)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

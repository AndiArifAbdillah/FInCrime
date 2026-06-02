"""Layer 1 — Fraud Detection endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.common.schemas import Transaction, FraudPrediction
from ..dependencies import get_fraud_detector

router = APIRouter()


@router.post("/predict", response_model=FraudPrediction)
def predict_one(tx: Transaction, det=Depends(get_fraud_detector)):
    """Real-time fraud check on a single transaction."""
    try:
        return det.predict_one(tx)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/predict-batch", response_model=list[FraudPrediction])
def predict_batch(transactions: list[Transaction], det=Depends(get_fraud_detector)):
    if len(transactions) > 1000:
        raise HTTPException(status_code=400, detail="Batch size limit is 1000")
    try:
        return det.predict_batch(transactions)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

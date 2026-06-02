"""Audit log query endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from src.observability import audit_log

router = APIRouter()


@router.get("/v1/audit/stats")
def stats():
    return audit_log.stats()


@router.get("/v1/audit/events")
def events(
    event_type: Optional[str] = None,
    subject: Optional[str] = None,
    actor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    return {
        "events": audit_log.query(
            event_type=event_type, subject=subject, actor=actor, limit=limit,
        ),
    }


@router.post("/v1/audit/seed-demo")
def seed_demo():
    """Generate fake audit events for demo."""
    import random
    types = ["prediction", "report_generated", "case_status_change", "data_access"]
    actors = ["system", "officer_01", "officer_02", "compliance_lead"]
    layers = ["layer0", "layer1", "layer2", "layer3", "api"]
    for i in range(50):
        audit_log.record(
            event_type=random.choice(types),
            actor=random.choice(actors),
            subject=f"subject_{i:04d}",
            layer=random.choice(layers),
            action=random.choice(["score", "create", "update", "view"]),
            payload={"sample": True, "i": i},
            model_version="0.1.0",
        )
    return {"ok": True, **audit_log.stats()}

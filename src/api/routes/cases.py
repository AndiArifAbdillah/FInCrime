"""Case Management API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.cases import CaseStore, AlertLink, CaseStatus

router = APIRouter()
_store = CaseStore()


class CaseCreate(BaseModel):
    title: str
    subject_id: str
    subject_type: str = "wallet"
    assignee: str = "unassigned"
    description: str = ""


class StatusUpdate(BaseModel):
    status: str


class AssigneeUpdate(BaseModel):
    assignee: str


class AlertAdd(BaseModel):
    alert_type: str
    alert_ref: str
    severity: str = "medium"
    score: float = 0.0
    note: str = ""


class NoteAdd(BaseModel):
    author: str = "anonymous"
    note: str


@router.get("/list")
def list_cases(status: Optional[str] = None, limit: int = 50):
    return {
        "stats": _store.stats(),
        "cases": [c.__dict__ for c in _store.list(status=status, limit=limit)],
    }


@router.post("/create")
def create_case(payload: CaseCreate):
    c = _store.create(**payload.model_dump())
    return c.__dict__


@router.get("/{case_id}")
def get_case(case_id: str):
    c = _store.get(case_id)
    if not c:
        raise HTTPException(404, "Case not found")
    # serialize alerts properly
    d = c.__dict__.copy()
    d["alerts"] = [a.__dict__ for a in c.alerts]
    return d


@router.patch("/{case_id}/status")
def patch_status(case_id: str, payload: StatusUpdate):
    valid = {s.value for s in CaseStatus}
    if payload.status not in valid:
        raise HTTPException(400, f"Invalid status. Valid: {sorted(valid)}")
    ok = _store.update_status(case_id, payload.status)
    if not ok:
        raise HTTPException(404, "Case not found")
    return {"ok": True}


@router.patch("/{case_id}/assignee")
def patch_assignee(case_id: str, payload: AssigneeUpdate):
    ok = _store.assign(case_id, payload.assignee)
    if not ok:
        raise HTTPException(404, "Case not found")
    return {"ok": True}


@router.post("/{case_id}/alerts")
def add_alert(case_id: str, payload: AlertAdd):
    if not _store.get(case_id):
        raise HTTPException(404, "Case not found")
    _store.add_alert(case_id, AlertLink(**payload.model_dump()))
    return {"ok": True}


@router.post("/{case_id}/notes")
def add_note(case_id: str, payload: NoteAdd):
    if not _store.get(case_id):
        raise HTTPException(404, "Case not found")
    _store.add_note(case_id, payload.author, payload.note)
    return {"ok": True}


@router.post("/{case_id}/reports/{report_id}")
def link_report(case_id: str, report_id: str):
    if not _store.get(case_id):
        raise HTTPException(404, "Case not found")
    _store.link_report(case_id, report_id)
    return {"ok": True}

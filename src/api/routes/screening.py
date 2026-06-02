"""Screening endpoints: DTTOT/UN sanctions + Negative news."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.common.logger import get_logger
from src.integrations.sanctions_dttot import screen_name, screening_index, load_all_dttot
from src.integrations.news_screener import screen_entity

log = get_logger("api.screening")

router = APIRouter()


# Cache the DTTOT index (refresh on demand)
_dttot_index = None


def _get_index():
    global _dttot_index
    if _dttot_index is None:
        _dttot_index = screening_index()
    return _dttot_index


@router.get("/v1/screening/dttot/list")
def dttot_list_summary(limit: int = Query(20, ge=1, le=200)):
    """Return summary stats + sample of DTTOT entries."""
    entries = load_all_dttot()
    return {
        "total": len(entries),
        "indonesian_priority": sum(1 for e in entries if e.is_indonesian_priority),
        "by_type": {
            "individual": sum(1 for e in entries if e.list_type == "individual"),
            "entity": sum(1 for e in entries if e.list_type == "entity"),
        },
        "sample": [e.__dict__ for e in entries[:limit]],
    }


@router.get("/v1/screening/dttot/{name}")
def dttot_check(name: str):
    """Check a single name against DTTOT + UN consolidated list."""
    idx = _get_index()
    hit = screen_name(name, idx)
    return {
        "name": name,
        "match": hit is not None,
        "entry": hit.__dict__ if hit else None,
        "index_size": len(idx),
    }


@router.post("/v1/screening/dttot/refresh")
def dttot_refresh():
    """Force-refresh the DTTOT/UN list (re-download)."""
    from src.integrations.sanctions_dttot import download_un_list
    global _dttot_index
    try:
        download_un_list(force=True)
        _dttot_index = screening_index()
        return {"ok": True, "index_size": len(_dttot_index)}
    except Exception as e:
        raise HTTPException(503, f"Refresh failed: {e}")


@router.get("/v1/screening/news/{entity_name}")
def news_screen(entity_name: str,
                min_score: float = Query(0.0, ge=0, le=1),
                limit: int = Query(15, ge=1, le=50)):
    """Scrape Indonesian news for mentions of `entity_name` + sentiment score."""
    hits = screen_entity(entity_name, min_score=min_score, limit=limit)
    return {
        "entity": entity_name,
        "hit_count": len(hits),
        "max_score": max((h.sentiment_score for h in hits), default=0.0),
        "hits": [h.__dict__ for h in hits],
    }

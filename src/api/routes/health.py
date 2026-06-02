"""Healthcheck endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Meta"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    """Readiness probe — could check model files exist, DB connectivity, etc."""
    from src.common.config import settings
    models_dir = settings.app_models_dir
    return {
        "status": "ready" if models_dir.exists() else "not_ready",
        "models_dir": str(models_dir),
        "env": settings.app_env,
    }

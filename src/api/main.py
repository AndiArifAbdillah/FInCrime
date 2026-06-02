"""FinCrime — FastAPI service entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.common.config import settings
from src.common.logger import get_logger
from .routes import (
    risk, fraud, tracing, reports, health, overview, cases, alerts_ws,
    screening, private_sector, multichain, monitoring, audit,
)
from src.observability import setup_prometheus

log = get_logger("api.main")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("api.startup", env=settings.app_env)
    yield
    log.info("api.shutdown")


app = FastAPI(
    title="FinCrime API",
    description="End-to-End Financial Crime Intelligence System for Indonesia",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(risk.router, prefix="/v1/risk", tags=["Layer 0 — Risk Scoring"])
app.include_router(fraud.router, prefix="/v1/fraud", tags=["Layer 1 — Fraud Detection"])
app.include_router(tracing.router, prefix="/v1/tracing", tags=["Layer 2 — Crypto Tracing"])
app.include_router(reports.router, prefix="/v1/reports", tags=["Layer 3 — Regtech Reports"])
app.include_router(overview.router, tags=["Dashboard aggregates"])
app.include_router(cases.router, prefix="/v1/cases", tags=["Case Management"])
app.include_router(screening.router, tags=["Sanctions & News Screening"])
app.include_router(alerts_ws.router, tags=["WebSocket alerts"])
app.include_router(private_sector.router, tags=["Private Sector AML"])
app.include_router(multichain.router, tags=["Multi-chain Crypto"])
app.include_router(monitoring.router, tags=["Model Monitoring"])
app.include_router(audit.router, tags=["Audit Log"])

# Prometheus /metrics + request tracking middleware
setup_prometheus(app)

# Serve the web UI (static files + index.html at /)
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.exception_handler(Exception)
async def _err_handler(request, exc: Exception):
    log.error("api.unhandled", path=str(request.url.path), error=str(exc))
    return JSONResponse(status_code=500, content={"detail": f"Internal error: {exc}"})


@app.get("/", tags=["Meta"])
def root():
    """Serve the web UI if available, else JSON banner."""
    idx = WEB_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return JSONResponse({
        "service": "fincrime-ai",
        "version": "0.1.0",
        "layers": ["layer0_risk_scoring", "layer1_fraud_detection",
                   "layer2_gnn_tracing", "layer3_regtech"],
        "docs": "/docs",
    })


@app.get("/api", tags=["Meta"])
def api_banner():
    return {
        "service": "fincrime-ai",
        "version": "0.1.0",
        "docs": "/docs",
        "ui": "/",
    }

"""Prometheus metrics for FinCrime."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from src.common.logger import get_logger

log = get_logger("metrics.prom")

# Use prometheus_client if available, else no-op stubs
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST,
    )
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


class _Stub:
    def __getattr__(self, _name):
        return lambda *a, **k: self
    def __call__(self, *a, **k): return self
    def labels(self, *a, **k): return self
    def observe(self, *a, **k): pass
    def inc(self, *a, **k): pass
    def set(self, *a, **k): pass
    def time(self):
        class _C:
            def __enter__(s): return s
            def __exit__(s, *a): pass
        return _C()


if _AVAILABLE:
    METRICS = {
        "predictions_total": Counter(
            "fincrime_predictions_total",
            "Total predictions made by FinCrime models",
            ["layer", "model_version"],
        ),
        "alerts_total": Counter(
            "fincrime_alerts_total",
            "Total alerts raised",
            ["layer", "severity"],
        ),
        "prediction_latency": Histogram(
            "fincrime_prediction_latency_seconds",
            "Inference latency per layer",
            ["layer"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        ),
        "reports_total": Counter(
            "fincrime_reports_total",
            "Total LTKM/LTKT reports generated",
            ["report_type"],
        ),
        "cases_open": Gauge(
            "fincrime_cases_open",
            "Number of investigation cases by status",
            ["status"],
        ),
        "api_requests_total": Counter(
            "fincrime_api_requests_total",
            "Total API requests",
            ["method", "endpoint", "status"],
        ),
        "api_request_duration": Histogram(
            "fincrime_api_request_duration_seconds",
            "API request duration",
            ["method", "endpoint"],
        ),
    }
else:
    METRICS = {k: _Stub() for k in [
        "predictions_total", "alerts_total", "prediction_latency",
        "reports_total", "cases_open", "api_requests_total",
        "api_request_duration",
    ]}


def setup_prometheus(app):
    """Mount /metrics endpoint and a request-tracking middleware."""
    if not _AVAILABLE:
        log.warning("prometheus_client not installed — /metrics disabled")
        return app

    from fastapi import Response
    from starlette.middleware.base import BaseHTTPMiddleware

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    class _RequestMetrics(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            t0 = time.perf_counter()
            response = await call_next(request)
            elapsed = time.perf_counter() - t0
            ep = request.url.path
            # Bucket path to avoid high cardinality
            if ep.startswith("/v1/"):
                parts = ep.split("/")
                ep = "/".join(parts[:3]) + ("/*" if len(parts) > 3 else "")
            METRICS["api_requests_total"].labels(
                method=request.method, endpoint=ep, status=response.status_code,
            ).inc()
            METRICS["api_request_duration"].labels(
                method=request.method, endpoint=ep,
            ).observe(elapsed)
            return response

    app.add_middleware(_RequestMetrics)
    log.info("prometheus.metrics_mounted", path="/metrics")
    return app

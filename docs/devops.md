# DevOps & MLOps Operations Guide

End-to-end production operations for FinCrime.

## Architecture

```
                    ┌──────────────────────────────────┐
                    │       FinCrime API (k8s)       │
                    │   ┌──────────────────────────┐    │
                    │   │ /metrics  /v1/*  WS      │    │
                    │   └──────────┬───────────────┘    │
                    └──────────────┼───────────────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        ▼              ▼           ▼           ▼              ▼
   ┌─────────┐  ┌────────────┐  ┌──────┐  ┌──────────┐  ┌──────────┐
   │ Neo4j   │  │ Prometheus │  │MLflow│  │ Airflow  │  │ Grafana  │
   │ :7474   │  │ :9090      │  │:5000 │  │ :8080    │  │ :3000    │
   └─────────┘  └─────┬──────┘  └──────┘  └──────────┘  └─────┬────┘
                      │                                        │
                      └────────────────────────────────────────┘
                       PromQL queries  ────────────────────►
```

## Local stack

```powershell
docker-compose up -d
```

| URL | Service | Login |
|-----|---------|-------|
| http://localhost:8000/ | FinCrime UI | — |
| http://localhost:8000/metrics | Prometheus scrape target | — |
| http://localhost:9090/ | Prometheus | — |
| http://localhost:3000/ | Grafana | admin / fincrime-admin |
| http://localhost:5000/ | MLflow | — |
| http://localhost:7474/ | Neo4j | neo4j / fincrime-dev-password |

## Observability

### Prometheus metrics exposed

| Metric | Labels | Type |
|--------|--------|------|
| `fincrime_predictions_total` | layer, model_version | Counter |
| `fincrime_alerts_total` | layer, severity | Counter |
| `fincrime_prediction_latency_seconds` | layer | Histogram |
| `fincrime_reports_total` | report_type | Counter |
| `fincrime_cases_open` | status | Gauge |
| `fincrime_api_requests_total` | method, endpoint, status | Counter |
| `fincrime_api_request_duration_seconds` | method, endpoint | Histogram |

### Grafana dashboards

Import [deployment/grafana/fincrime_overview.json](../deployment/grafana/fincrime_overview.json) to get:
- Predictions/sec, alert rate, p95 latency, reports/24h (stat panels)
- Predictions by layer + Alerts by severity (timeseries)
- API rate + latency by endpoint (timeseries)

### Alerting rules

[deployment/prometheus/alerts.yml](../deployment/prometheus/alerts.yml) fires:
- **HighAlertRate** — alert rate >50% for 10min → model degradation
- **HighInferenceLatency** — p95 >1s → scaling needed
- **APIErrorRateHigh** — 5xx >5% → incident

Route to Slack/PagerDuty via Alertmanager (config not included).

## MLflow workflow

### Local

```powershell
.\fc python scripts\train_with_mlflow.py
.\fc python -m mlflow ui --backend-store-uri file:./data/mlruns
# Open http://localhost:5000
```

### Per-run captured

- **Params**: model type, hyperparameters
- **Metrics**: ROC AUC, PR AUC, F1, training loss
- **Artifacts**: model bundle (joblib/pt), meta.json
- **Model registry**: registers as `fincrime-layer{N}-{version}`

### Promote model to production

```bash
mlflow models serve -m "models:/fincrime-layer0/Production" -p 9090
```

## Airflow DAGs

| DAG | Schedule | What |
|-----|----------|------|
| `fincrime_ofac_refresh` | daily 02:00 | OFAC + UN list refresh, apply to entities |
| `fincrime_retrain_weekly` | weekly Mon 03:00 | Retrain all layers, log to MLflow |
| `fincrime_drift_check` | every 6h | Compute PSI, alert if high |
| `fincrime_news_screening` | every 4h | Scrape negative news, audit |

### Run locally

```bash
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow_dags
pip install apache-airflow==2.10.3
airflow db init
airflow standalone
```

## CI/CD

[.github/workflows/ci.yml](../.github/workflows/ci.yml) runs on every push:
1. Install deps + generate sample data (500 entities, fast)
2. Train Layer 0 + 1 (no AE for speed)
3. Unit tests (pytest -m "not slow")
4. API smoke tests (TestClient on key endpoints)
5. Wave 1 + 2 smoke scripts
6. Ruff lint
7. On `main`: build Docker images (api, dashboard)

[.github/workflows/security.yml](../.github/workflows/security.yml):
- Bandit static analysis (every push + weekly)
- pip-audit for known CVEs

## Audit log

Every prediction / report / case change is recorded in `data/fincrime_audit.db`.
Query via API:

```bash
curl http://localhost:8000/v1/audit/events?event_type=prediction&limit=20
curl http://localhost:8000/v1/audit/stats
```

Required by **POJK No.12/2024 Pasal 8** and **UU PDP No.27/2022 Pasal 26**.

## Disaster recovery

| Component | Backup strategy |
|-----------|-----------------|
| Neo4j | `neo4j-admin database backup` → S3 daily |
| SQLite (cases, audit, metrics) | Litestream to S3 continuous |
| Model registry | MLflow → S3 backend |
| Configuration | GitHub Actions deploys from `main` |
| Secrets | Vault / cloud KMS (NEVER in git) |

## Scaling

| Layer | Bottleneck | Mitigation |
|-------|-----------|------------|
| Layer 0 | CPU bound | HPA + multiple replicas |
| Layer 1 | I/O (Kafka) | Add partitions |
| Layer 2 | Memory (graph) | Neo4j read replicas + caching |
| Layer 3 | PDF rendering | Async queue |
| Web UI | Stateless | CDN cache static + CloudFront |

# FinCrime — Deployment Guide

## Stages

| Stage | Purpose | Target |
|-------|---------|--------|
| **Local dev** | engineer's laptop | `python -m venv .venv && pip install -r requirements.txt` |
| **Docker compose** | integration testing | `docker-compose up --build` |
| **Staging / Sandbox (OJK)** | UAT against partner institution data | k8s on internal cloud |
| **Production** | live | k8s on managed cloud (GKE / EKS / IBM Cloud), with PPATK & OJK integration |

## 1. Local development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python scripts/generate_sample_data.py
python scripts/train_all_models.py
python scripts/run_pipeline.py    # end-to-end demo

uvicorn src.api.main:app --reload --port 8000
streamlit run src/dashboard/app.py
```

## 2. Docker compose (full stack)

```bash
docker-compose up --build
```

Brings up:
- `api` — FastAPI on :8000
- `dashboard` — Streamlit on :8501
- `neo4j` — :7474 (UI), :7687 (bolt)
- `kafka` + `zookeeper`

**First-run model train inside the container:**
```bash
docker exec -it fincrime-api python scripts/generate_sample_data.py
docker exec -it fincrime-api python scripts/train_all_models.py
docker exec -it fincrime-api python scripts/setup_neo4j.py
```

## 3. Kubernetes (production)

Manifests live in `deployment/kubernetes/`.

```bash
# 1. Create namespace + secrets
kubectl create namespace fincrime
kubectl -n fincrime create secret generic fincrime-secrets \
    --from-literal=API_SECRET_KEY=$(openssl rand -hex 32) \
    --from-literal=NEO4J_PASSWORD=$(openssl rand -hex 24) \
    --from-literal=ETHERSCAN_API_KEY=$ETHERSCAN_KEY \
    --from-literal=PPATK_API_KEY=$PPATK_KEY

# 2. Apply manifests
kubectl -n fincrime apply -f deployment/kubernetes/

# 3. Verify
kubectl -n fincrime get pods,svc,ingress
```

### Horizontal pod autoscaler (recommended)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: fincrime-api-hpa, namespace: fincrime }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fincrime-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } }
```

## 4. Model store

Production model artifacts should NOT be baked into images. Instead:

```
s3://fincrime-models/<env>/<model_name>/<version>/model.joblib
                                                 /model.meta.json
```

Pods mount this via an initContainer that pulls the latest tag.

## 5. Observability

- **Logs:** structlog → stdout → Fluent Bit → Loki/Elastic.
- **Metrics:** Prometheus endpoint `/metrics` (add via `prometheus-fastapi-instrumentator`).
- **Tracing:** OpenTelemetry instrumentation on the FastAPI app.

## 6. Disaster recovery

- **Neo4j:** daily snapshot to S3 (`neo4j-admin database backup`).
- **Kafka:** 7-day retention + offsite mirror.
- **Models:** versioned + immutable in S3 with object-lock.

## 7. Roadmap to production

| Milestone | Target date | Owner |
|-----------|-------------|-------|
| MVP demo + Stage 2 PIDI | 2026-06 | All |
| Partner integration (1 bank UAT) | 2026-09 | Andi + Rambu |
| OJK regulatory sandbox entry | 2026-Q4 | Andi |
| PPATK GRIPS pilot | 2027-Q1 | TB Fikri |
| Production GA | 2027-Q3 | All |

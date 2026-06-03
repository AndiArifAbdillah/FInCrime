# FinCrime — End-to-End Financial Crime Intelligence System

[![Status](https://img.shields.io/badge/status-prototype-blue)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-Proprietary-red)]()

An integrated, real-time AI platform to detect and prevent financial crimes in Indonesia: fraud, money laundering, and illicit crypto flows. Built for Bank Indonesia's PIDI challenge, aligned with **POJK No.12/2024**, **UU PDP No.27/2022**, and **FATF** recommendations.

---

## Architecture Overview

```
                ┌─────────────────────────────────────────────┐
                │           INGESTION (Apache Kafka)          │
                │   Banks  •  E-Wallets  •  Blockchain RPC    │
                └──────────────────────┬──────────────────────┘
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
┌──────────────┐              ┌────────────────┐              ┌─────────────────┐
│  LAYER 0     │              │   LAYER 1      │              │   LAYER 2       │
│ Risk Scoring │ ───────────▶ │ Fraud Detection│ ───────────▶ │  GNN Tracing    │
│ XGBoost+SHAP │              │  IF + AutoEnc  │              │ GraphSAGE+Neo4j │
└──────────────┘              └────────────────┘              └────────┬────────┘
                                                                       │
                                                              ┌────────▼────────┐
                                                              │    LAYER 3      │
                                                              │  Regtech / AML  │
                                                              │ Jinja2 LTKM/LTKT│
                                                              └────────┬────────┘
                                                                       │
                                                              ┌────────▼────────┐
                                                              │   Dashboard +   │
                                                              │  PPATK Export   │
                                                              └─────────────────┘
```

| Layer | Component | Tech | Latency target |
|-------|-----------|------|----------------|
| 0 | Risk Scoring | XGBoost + SHAP | < 100 ms |
| 1 | Fraud Detection | Isolation Forest + Autoencoder (PyTorch) | < 500 ms |
| 2 | Crypto Tracing | GraphSAGE (PyG) + Neo4j | < 2 s / subgraph |
| 3 | Regtech Reports | Jinja2 + WeasyPrint | < 5 min end-to-end |

---

## Quick Start

### Windows / PowerShell (verified on Python 3.14)

```powershell
# 1. Create venv if missing
py -m venv .venv

# 2. Activate it
.\.venv\Scripts\Activate.ps1
#   (if blocked: powershell -ExecutionPolicy Bypass -File .\setup.ps1)

# 3. Install (use core requirements on Python 3.14 — full reqs need 3.11/3.12)
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-core.txt

# 4. Generate sample data + train all models
python scripts\generate_sample_data.py
python scripts\train_all_models.py

# 5. Run end-to-end pipeline demo
python scripts\run_pipeline.py

# 6. Start the API
python -m uvicorn src.api.main:app --reload --port 8000

# 7. Start the dashboard (separate terminal, venv activated)
python -m streamlit run src\dashboard\app.py
```

### Linux / Mac

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt    # full reqs incl. torch+pyg
python scripts/generate_sample_data.py
python scripts/train_all_models.py
python scripts/run_pipeline.py
uvicorn src.api.main:app --reload --port 8000
streamlit run src/dashboard/app.py
```

API docs: http://localhost:8000/docs
Dashboard: http://localhost:8501

### Optional: enable Layer 2 (GNN) + SHAP + PDF reports

On Python 3.14 these may not have wheels yet. If you need them, use **Python 3.11 or 3.12** and install the full `requirements.txt`. Or upgrade later:

```powershell
python -m pip install torch shap weasyprint torch-geometric
```

### Disk full on C:\? (common Windows issue)

If pip errors with `No space left on device`, redirect temp to a drive with free space:

```powershell
$env:TMP = "D:\pip-tmp"; $env:TEMP = "D:\pip-tmp"
mkdir D:\pip-tmp -Force | Out-Null
python -m pip install --cache-dir D:\pip-cache -r requirements-core.txt
```

---

## Docker (one-shot full stack)

```bash
docker-compose up --build
```

Services:
- `api` — FastAPI on :8000
- `dashboard` — Streamlit on :8501
- `neo4j` — graph DB on :7474 / :7687
- `kafka` + `zookeeper` — ingestion bus

---

## Project Structure

```
FInCrime/
├── src/
│   ├── common/              # shared schemas, config, logger
│   ├── ingestion/           # Kafka producers/consumers, connectors
│   ├── layer0_risk_scoring/ # XGBoost + SHAP
│   ├── layer1_fraud_detection/ # Isolation Forest + Autoencoder
│   ├── layer2_gnn_tracing/  # GraphSAGE + Neo4j
│   ├── layer3_regtech/      # LTKM/LTKT report generator
│   ├── api/                 # FastAPI service
│   └── dashboard/           # Streamlit UI
├── data/
│   ├── raw/                 # ingested raw
│   ├── processed/           # feature stores
│   ├── sample/              # synthetic demo data
│   └── models/              # trained model artifacts (.pkl, .pt)
├── scripts/
│   ├── generate_sample_data.py
│   ├── train_all_models.py
│   └── run_pipeline.py
├── tests/                   # pytest suite
├── docker/                  # Dockerfiles per service
├── deployment/kubernetes/   # k8s manifests
├── docs/                    # architecture, API, deployment
└── notebooks/               # exploratory analysis
```

---

## Team

| Name | Institution | Role |
|------|-------------|------|
| Andi Arif Abdillah | Universitas Gunadarma | Project Lead, Layer 2 (GNN) |
| Raya Sesan Firdaus | Universitas Gunadarma | Layer 0 (Risk Scoring) |
| Rambu Ilalang | Universitas Gunadarma | Layer 1 + MLOps |
| TB Muhammad Fikri Arsyad | Universitas Sultan Ageng Tirtayasa | Layer 3 + Dashboard |

---

## Connect to Real Data

To replace synthetic data with real sources (OFAC sanctions, Etherscan, bank CSVs), see [docs/real_data_guide.md](docs/real_data_guide.md).

Quick commands:
```powershell
python scripts\fetch_sanctions.py                                # OFAC list (free)
python scripts\fetch_real_blockchain.py                          # Etherscan (free API key)
python scripts\import_bank_csv.py statement.csv --account 1234   # Bank CSV
python scripts\score_real_data.py                                # Fraud scoring
```

## Compliance & Regulatory Mapping

- **POJK No.12/2024** — proactive anti-fraud strategy
- **UU PDP No.27/2022** — data minimization, end-to-end encryption, audit logs
- **PPATK LTKM/LTKT** — automated report generation
- **FATF Recommendations 10, 11, 20** — beneficial ownership tracing, suspicious transaction reporting
- **POJK No.27/2024** — crypto asset oversight (Bappebti → OJK transition)

---

## License

Proprietary — FinCrime Team, 2026. All rights reserved.

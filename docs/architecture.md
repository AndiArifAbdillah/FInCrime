# FinCrime — Architecture

## 1. High-level overview

FinCrime is a microservice-style, API-driven AI platform with four ML/AI layers wired together by a Kafka-based event bus.

```
            ┌──────────────────────────────────────────────────────────┐
            │                  INGESTION                                │
            │ ┌─────────────┐ ┌─────────────┐ ┌────────────────────┐    │
            │ │  Banks       │ │ E-Wallets   │ │ Blockchain RPC     │    │
            │ │  (REST/SFTP) │ │  (REST)     │ │ (Etherscan / web3) │    │
            │ └──────┬──────┘ └──────┬──────┘ └─────────┬──────────┘    │
            │        ▼               ▼                   ▼               │
            │             Apache Kafka (transactions topic)              │
            └────────────────────────┬─────────────────────────────────┘
                                     │
   ┌─────────────────────────────────┼─────────────────────────────────┐
   │ PROCESSING                      ▼                                  │
   │ ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────┐ │
   │ │ Layer 0              │  │ Layer 1              │  │ Layer 2     │ │
   │ │ Entity Risk Scoring  │  │ Tx Fraud Detection   │  │ GNN Tracing │ │
   │ │ XGBoost + SHAP       │  │ IsoForest + Autoenc  │  │ GraphSAGE   │ │
   │ │ < 100 ms             │  │ < 500 ms             │  │ Neo4j       │ │
   │ └──────────┬───────────┘  └──────────┬───────────┘  └──────┬─────┘ │
   │            │                         │                       │      │
   │            └──────────┬──────────────┘                       │      │
   │                       ▼                                       │      │
   │                  ALERT STREAM (Kafka)                         │      │
   └──────────────────────────────────────────────────────────────┼─────┘
                                                                  ▼
                          ┌──────────────────────────────────────────┐
                          │ Layer 3 — Regtech                         │
                          │ Jinja2 templates → LTKM/LTKT/HTML/JSON    │
                          └──────────────────┬───────────────────────┘
                                             ▼
                          ┌───────────────────────────────────────────┐
                          │ Outputs                                    │
                          │ • Compliance dashboard (Streamlit)         │
                          │ • PPATK GRIPS submission (REST + signed)   │
                          │ • Investigation graph viewer               │
                          └───────────────────────────────────────────┘
```

## 2. Layer-by-layer

### Layer 0 — Entity Risk Scoring
- **Goal:** assign a 0–100 risk score to every customer / wallet *before* it ever transacts.
- **Model:** XGBoost binary classifier with `scale_pos_weight` for class imbalance.
- **Features:** 17 numeric/boolean/derived features (KYC level, txn velocity, volume, country, etc.).
- **Explainability:** SHAP `TreeExplainer` returns top-5 contributing factors per prediction — required by POJK No.12/2024.
- **Latency budget:** < 100 ms p95, single-entity inference; SHAP doubles this in the worst case.

### Layer 1 — Real-time Fraud Detection
- **Goal:** flag individual transactions as anomalous in < 500 ms.
- **Models:** ensemble of `sklearn.IsolationForest` + tabular **PyTorch autoencoder** with 95th-percentile reconstruction-error threshold.
- **Combined score:** `0.5 * IF_score + 0.5 * AE_score`, both normalized to [0,1].
- **Rule overlay:** deterministic rules from `rules.py` (smurfing, volume spike, high-risk jurisdiction, blacklist hit).
- **Output:** `FraudPrediction` with `is_anomaly`, score, and triggered rules.

### Layer 2 — GNN Crypto Tracing
- **Goal:** uncover layering / smurfing patterns invisible to flat ML.
- **Model:** 2-layer **GraphSAGE** (mean aggregation) over a directed wallet graph stored in **Neo4j**.
- **Inference:** node-classification → per-wallet fraud probability.
- **Pattern detector:** DFS-based smurfing-chain finder in `patterns.py` (sub-50M IDR chained transfers).
- **Subgraph view:** k-hop ego-net for the investigation UI.

### Layer 3 — Regtech / AML/CFT
- **Goal:** reduce LTKM/LTKT generation from days to minutes.
- **Templates:** Jinja2 — `ltkm_template.html.j2`, `ltkt_template.html.j2`, modeled after PPATK GRIPS structure.
- **Outputs:** HTML (compliance review), JSON (machine submission), optional PDF (WeasyPrint).
- **Triggers:**
  - LTKM: automatic when Layer 2 layering score ≥ 0.6 OR Layer 0 risk ≥ critical.
  - LTKT: same-day cash transactions aggregating ≥ IDR 500M.

## 3. Data flow

1. Connector pulls raw events → normalizes to canonical `Transaction` schema.
2. `TransactionProducer` publishes to `fincrime.<channel>.transactions`.
3. `TransactionConsumer` (Layer 1 worker) consumes → calls `FraudDetector.predict_one`.
4. Anomalous transactions → enqueue Layer 2 trace job.
5. Layer 2 walks the Neo4j graph and updates `layering_score` per wallet.
6. Above threshold → Layer 3 auto-generates the LTKM and notifies compliance officer.
7. Officer reviews on Streamlit dashboard → signs → submits to PPATK.

## 4. Security & compliance

| Concern | Mitigation |
|---------|------------|
| Data minimization (UU PDP) | Only the features listed in `Entity` & `Transaction` schemas are ingested. No raw PII beyond pseudonymous IDs. |
| Encryption in transit | Kafka + Neo4j with TLS in production; Ingress with cert-manager (Let's Encrypt). |
| Encryption at rest | Cloud-managed KMS volumes for Neo4j and model store. |
| Audit log | Every prediction / report generation persisted with timestamp + model version (`structlog` JSON output → SIEM). |
| RBAC | API SecretRef gated; compliance officer roles separated from analyst roles. |
| Model governance | Each model checkpoint persists a `.meta.json` (metrics, features, version). Re-training requires re-validation against the holdout slice. |
| GRIPS submission integrity | Reports include institution code, officer ID, generated_at; PDF + JSON signed before transmission (out of prototype scope). |

## 5. Scalability targets

| Layer | Throughput per replica | Scaling strategy |
|-------|------------------------|------------------|
| Layer 0 | 5k req/s | Stateless API, horizontal pod autoscaler |
| Layer 1 | 2k tx/s | Stateless; Kafka partitions = replicas |
| Layer 2 | 50 traces/s | Caches loaded graph; Neo4j read replicas |
| Layer 3 | 100 reports/min | Stateless; Jinja2 cheap; PDF rendering is the bottleneck |

# FinCrime — REST API Reference

Base URL (local): `http://localhost:8000`
OpenAPI docs: `http://localhost:8000/docs`

All endpoints accept and return JSON. Authentication (Bearer token) is configured via `API_SECRET_KEY` in `.env` and enforced by the API gateway in production.

---

## Meta

| Method | Path     | Description |
|--------|----------|-------------|
| GET    | `/`      | Service banner |
| GET    | `/health`| Liveness probe |
| GET    | `/ready` | Readiness probe |

---

## Layer 0 — Risk Scoring

### `POST /v1/risk/score`

Score a single entity, returning top-5 SHAP factors.

**Request body:** `Entity`
```json
{
  "entity_id": "IND_000123",
  "entity_type": "individual",
  "country": "ID",
  "age_days": 800,
  "kyc_level": 1,
  "txn_count_30d": 84,
  "total_volume_30d": 2400000000,
  "avg_tx_amount": 28571000,
  "distinct_counterparties_30d": 23,
  "pep_flag": false,
  "sanction_flag": false,
  "has_crypto_activity": true
}
```

**Response:** `RiskScore`
```json
{
  "entity_id": "IND_000123",
  "score": 78.42,
  "level": "high",
  "top_factors": [
    {"feature": "total_volume_30d", "value": 2400000000, "contribution": 0.41},
    {"feature": "has_crypto_activity", "value": 1, "contribution": 0.28}
  ],
  "model_version": "0.1.0",
  "computed_at": "2026-05-21T10:42:11"
}
```

### `POST /v1/risk/score-batch`
Same body as `/score` but as an array. Max 1,000 entities per call.

---

## Layer 1 — Fraud Detection

### `POST /v1/fraud/predict`

```json
{
  "tx_id": "TX_000000001",
  "channel": "bank",
  "timestamp": "2026-05-21T10:45:00",
  "sender_id": "IND_000123",
  "receiver_id": "CORP_00001",
  "amount_idr": 49000000,
  "is_high_risk_jurisdiction": false
}
```

Response includes `anomaly_score`, `is_anomaly`, and `triggered_rules` (e.g., `smurfing`).

### `POST /v1/fraud/predict-batch`
Array, max 1,000.

---

## Layer 2 — Crypto Tracing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/tracing/wallet/{wallet_id}/score` | GNN fraud probability for a wallet |
| GET | `/v1/tracing/wallet/{wallet_id}/trace?hops=2` | Full subgraph + layering detection |

Response of `/trace` is a `GraphTraceResult` with `layering_score`, `flagged_wallets`, `pattern_types`, and a human-readable `explanation`.

---

## Layer 3 — Regtech / PPATK

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/reports/ltkm/auto/{wallet_id}` | Generate an LTKM automatically from a Layer 2 trace |
| POST | `/v1/reports/ltkm` | Generate an LTKM manually |
| POST | `/v1/reports/ltkt` | Generate an LTKT (must total ≥ IDR 500M) |
| GET  | `/v1/reports/{report_id}/preview` | HTML preview in-browser |
| GET  | `/v1/reports/{report_id}/download?fmt=json` | Download JSON / HTML / PDF |

---

## Error model

```json
{ "detail": "Error message" }
```

| Code | Meaning |
|------|---------|
| 400 | Validation error (e.g., batch too large, LTKT below threshold) |
| 404 | Report or wallet not found |
| 500 | Internal error |
| 503 | Model artifact missing — train first |

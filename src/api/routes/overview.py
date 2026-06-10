"""Aggregated metrics for the dashboard overview page + entities + reports list."""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Depends

from src.common.config import settings
from src.common.utils import row_to_entity

from ..dependencies import get_risk_scorer, get_fraud_detector

router = APIRouter()


@router.get("/v1/overview/metrics")
def overview_metrics():
    """Aggregated dashboard metrics from on-disk sample data + recent computations."""
    sample_dir = settings.app_data_dir / "sample"
    reports_dir = settings.app_data_dir / "reports"
    entities_csv = sample_dir / "entities.csv"
    transactions_csv = sample_dir / "transactions.csv"

    metrics = {
        "transactions_total": 0,
        "transactions_today_pct": "—",
        "alerts_active": 0,
        "alerts_critical": 0,
        "entities_high_risk": 0,
        "entities_total": 0,
        "reports_total": 0,
        "reports_ltkm": 0,
        "reports_ltkt": 0,
        "layer_status": {"l0": "Aktif", "l1": "Aktif", "l2": "Aktif", "l3": "Aktif"},
        "recent_alerts": [],
        "volume_7d": [],
    }

    # Transactions
    if transactions_csv.exists():
        df = pd.read_csv(transactions_csv)
        metrics["transactions_total"] = int(len(df))
        if "is_fraud" in df.columns:
            metrics["alerts_active"] = int(df["is_fraud"].sum())
            metrics["alerts_critical"] = int(((df["is_fraud"] == 1) &
                                              (df["amount_idr"] >= 500_000_000)).sum())
        # Volume 7d — last 7 days bucketing
        try:
            df["ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["ts"])
            now = df["ts"].max()
            buckets = []
            for i in range(6, -1, -1):
                day = (now - timedelta(days=i)).date()
                buckets.append(int(df[df["ts"].dt.date == day]["amount_idr"].count()))
            metrics["volume_7d"] = buckets
        except Exception:
            pass

    # Entities
    if entities_csv.exists():
        ent = pd.read_csv(entities_csv)
        metrics["entities_total"] = int(len(ent))
        if "is_fraud" in ent.columns:
            metrics["entities_high_risk"] = int(ent["is_fraud"].sum())

    # Reports
    if reports_dir.exists():
        htmls = sorted(reports_dir.glob("*.html"), reverse=True)
        metrics["reports_total"] = len(htmls)
        metrics["reports_ltkm"] = sum(1 for p in htmls if p.stem.startswith("LTKM"))
        metrics["reports_ltkt"] = sum(1 for p in htmls if p.stem.startswith("LTKT"))

    # Recent alerts (from latest reports)
    if reports_dir.exists():
        recent = sorted(reports_dir.glob("*.html"),
                        key=lambda p: p.stat().st_mtime, reverse=True)[:4]
        for p in recent:
            mt = datetime.fromtimestamp(p.stat().st_mtime)
            metrics["recent_alerts"].append({
                "severity": "critical" if "LTKM" in p.stem else "medium",
                "title": p.stem,
                "subtitle": f"{p.stem.split('-')[0]} · {mt.strftime('%d %b %H:%M')}",
            })

    # Layer status badges (string for display)
    metrics["layer_status"] = {
        "l0": "Aktif", "l1": "Aktif",
        "l2": "Aktif (GNN)" if (settings.app_models_dir / "layer2_graphsage.pt").exists()
              else "Aktif (heuristic)",
        "l3": f"{metrics['reports_total']} laporan",
    }

    return metrics


# ============================================================
# Entities (Layer 0)
# ============================================================
@router.get("/v1/entities/top")
def top_entities(limit: int = Query(12, ge=1, le=100),
                 scorer=Depends(get_risk_scorer)):
    """Return top-risk entities scored by the live XGBoost model."""
    entities_csv = settings.app_data_dir / "sample" / "entities.csv"
    if not entities_csv.exists():
        raise HTTPException(404, "entities.csv not found — run `.\\fc data` first")

    df = pd.read_csv(entities_csv).head(500)  # cap for speed
    rows = []
    ents = []
    for _, r in df.iterrows():
        e = row_to_entity(r)
        if e is not None:
            ents.append(e)
    scored = scorer.score_batch(ents)
    for ent, sc in zip(ents, scored):
        rows.append({
            "entity_id": ent.entity_id,
            "entity_type": ent.entity_type,
            "country": ent.country,
            "score": float(sc.score),
            "level": str(sc.level),
        })
    rows.sort(key=lambda x: -x["score"])
    selected = rows[:limit]

    return {
        "total_entities": len(df),
        "high_count": sum(1 for r in rows if r["score"] >= 70),
        "medium_count": sum(1 for r in rows if 40 <= r["score"] < 70),
        "low_count": sum(1 for r in rows if r["score"] < 40),
        "entities": selected,
    }


@router.get("/v1/entities/{entity_id}/shap")
def entity_shap(entity_id: str, scorer=Depends(get_risk_scorer)):
    """Score one entity with full SHAP factor breakdown."""
    entities_csv = settings.app_data_dir / "sample" / "entities.csv"
    if not entities_csv.exists():
        raise HTTPException(404, "entities.csv not found")

    df = pd.read_csv(entities_csv)
    row = df[df["entity_id"] == entity_id]
    if row.empty:
        raise HTTPException(404, f"Entity {entity_id} not found")
    e = row_to_entity(row.iloc[0])
    if e is None:
        raise HTTPException(400, "Failed to parse entity")
    result = scorer.score_one(e, with_shap=True)
    from src.common.explain import explain_risk_score, humanize_shap_list
    verdict = explain_risk_score(float(result.score))
    return {
        "entity_id": entity_id,
        "score": float(result.score),
        "level": str(result.level),
        "factors": result.top_factors,
        "verdict": verdict,               # NEW — plain-language explanation
        "factors_plain": humanize_shap_list(result.top_factors),  # NEW
    }


# ============================================================
# Fraud (Layer 1)
# ============================================================
@router.get("/v1/fraud/recent-alerts")
def fraud_recent_alerts(limit: int = Query(12, ge=1, le=100),
                        sample: int = Query(200, ge=10, le=2000),
                        det=Depends(get_fraud_detector)):
    """Score a recent batch of transactions and return the top anomalies."""
    from src.common.utils import rows_to_transactions
    transactions_csv = settings.app_data_dir / "sample" / "transactions.csv"
    if not transactions_csv.exists():
        raise HTTPException(404, "transactions.csv not found")
    df = pd.read_csv(transactions_csv).head(sample)
    txs = rows_to_transactions(r for _, r in df.iterrows())
    preds = det.predict_batch(txs)
    anomalies = sorted([p for p in preds if p.is_anomaly],
                       key=lambda p: -p.anomaly_score)[:limit]
    tx_by_id = {t.tx_id: t for t in txs}
    alerts = []
    for p in anomalies:
        tx = tx_by_id.get(p.tx_id)
        rules = ", ".join(str(r) for r in p.triggered_rules)
        title = f"{rules or 'Anomalous'}: {p.tx_id}"
        sub = "—"
        sender_id = None
        if tx:
            sender_id = tx.sender_id
            sub = (f"{tx.sender_id} → {tx.receiver_id} · "
                   f"Rp {tx.amount_idr:,.0f} · {tx.channel}")
        from src.common.explain import explain_fraud_score, humanize_rules_list
        verdict = explain_fraud_score(float(p.anomaly_score),
                                      [str(r) for r in p.triggered_rules])
        alerts.append({
            "tx_id": p.tx_id, "score": float(p.anomaly_score),
            "title": title, "subtitle": sub,
            "rules": [str(r) for r in p.triggered_rules],
            "rules_plain": humanize_rules_list([str(r) for r in p.triggered_rules]),  # NEW
            "sender_id": sender_id,
            "verdict": verdict,            # NEW — plain-language explanation
        })
    return {
        "total_scored": len(preds),
        "anomaly_count": sum(1 for p in preds if p.is_anomaly),
        "alerts": alerts,
    }


# ============================================================
# Tracing (Layer 2)
# ============================================================
@router.get("/v1/tracing/example-wallets")
def example_wallets(limit: int = 6):
    """Return some example seed wallets (2 fraud + 1 normal)."""
    entities_csv = settings.app_data_dir / "sample" / "entities.csv"
    if not entities_csv.exists():
        return {"wallets": []}
    df = pd.read_csv(entities_csv)
    wallets = df[df["entity_type"] == "wallet"]
    fraud = wallets[wallets.get("is_fraud", 0) == 1].head(2)["entity_id"].tolist()
    normal = wallets[wallets.get("is_fraud", 0) == 0].head(limit - len(fraud))["entity_id"].tolist()
    return {"wallets": fraud + normal}


# ============================================================
# Reports (Layer 3)
# ============================================================
@router.get("/v1/reports/list")
def list_reports():
    reports_dir = settings.app_data_dir / "reports"
    if not reports_dir.exists():
        return {"total": 0, "ltkm_count": 0, "ltkt_count": 0, "with_json": 0, "reports": []}
    out = []
    htmls = sorted(reports_dir.glob("*.html"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    for p in htmls:
        rid = p.stem
        formats = ["HTML"]
        if (reports_dir / f"{rid}.json").exists():
            formats.append("JSON")
        if (reports_dir / f"{rid}.pdf").exists():
            formats.append("PDF")
        out.append({
            "id": rid,
            "type": "LTKM" if rid.startswith("LTKM") else "LTKT" if rid.startswith("LTKT") else "OTHER",
            "created": datetime.fromtimestamp(p.stat().st_mtime).strftime("%d %b %Y %H:%M"),
            "formats": formats,
        })
    return {
        "total": len(out),
        "ltkm_count": sum(1 for r in out if r["type"] == "LTKM"),
        "ltkt_count": sum(1 for r in out if r["type"] == "LTKT"),
        "with_json": sum(1 for r in out if "JSON" in r["formats"]),
        "reports": out,
    }

"""Every 4 hours: scrape negative news about high-risk entities."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from airflow import DAG
from airflow.operators.python import PythonOperator


def scrape_news_for_high_risk():
    import pandas as pd
    from src.common.config import settings
    from src.integrations.news_screener import batch_screen
    from src.observability import audit_log

    csv = settings.app_data_dir / "sample" / "entities.csv"
    if not csv.exists():
        return {"skipped": True}
    df = pd.read_csv(csv)
    # Take the top 50 high-risk corporates only (avoid 1000s of HTTP calls)
    high_risk = df[(df.entity_type == "corporate") & (df.is_fraud == 1)].head(50)
    names = high_risk["entity_id"].tolist()
    hits = batch_screen(names, min_score=0.3)
    audit_log.record(
        event_type="news_screening",
        actor="airflow",
        subject=f"batch_{len(names)}",
        action="scrape",
        payload={"hits_per_entity": {k: len(v) for k, v in hits.items()}},
    )
    return {"entities_screened": len(names), "with_hits": len(hits)}


default_args = {
    "owner": "fincrime-ops",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "fincrime_news_screening",
    description="Scrape ID media for negative news on high-risk entities",
    schedule="0 */4 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["fincrime", "screening"],
) as dag:
    PythonOperator(task_id="scrape", python_callable=scrape_news_for_high_risk)

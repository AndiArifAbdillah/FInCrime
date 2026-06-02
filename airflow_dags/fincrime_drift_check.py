"""Drift check every 6h. Alerts compliance team if PSI > threshold."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from airflow import DAG
from airflow.operators.python import PythonOperator


def check_drift(**ctx):
    import pandas as pd
    from src.common.config import settings
    from src.monitoring import compute_feature_drift_report
    from src.observability import audit_log

    csv = settings.app_data_dir / "sample" / "entities.csv"
    if not csv.exists():
        return {"skipped": "no baseline data"}

    df = pd.read_csv(csv)
    # In production: compare baseline vs current window
    # Here: split data in half for demo
    n = len(df)
    rep = compute_feature_drift_report(df.iloc[:n//2], df.iloc[n//2:])
    audit_log.record(
        event_type="drift_check",
        actor="airflow",
        subject="layer0",
        action="compute_psi",
        payload={
            "overall_psi": rep.overall_psi,
            "severity": rep.overall_severity,
            "top_drifted": [d.feature for d in rep.feature_drifts[:5]],
        },
    )
    if rep.overall_severity == "high":
        print(f"[ALERT] PSI = {rep.overall_psi:.4f} (HIGH). Retraining advised.")
        # In production: send Slack/email/PagerDuty notification
    return {"psi": rep.overall_psi, "severity": rep.overall_severity}


default_args = {
    "owner": "fincrime-ops",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    "fincrime_drift_check",
    description="Compute PSI/KS drift every 6h",
    schedule="0 */6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["fincrime", "monitoring", "drift"],
) as dag:
    PythonOperator(task_id="check_drift", python_callable=check_drift)

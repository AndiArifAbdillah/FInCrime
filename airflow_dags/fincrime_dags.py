"""Apache Airflow DAGs for FinCrime scheduled operations.

Drop this file in your Airflow `dags/` folder (or set `AIRFLOW__CORE__DAGS_FOLDER`
to `./airflow_dags/`). All DAGs are stateless and safe to retry.

DAGs:
    fincrime_refresh_sanctions  — daily 04:00 WIB: refresh OFAC + UN list
    fincrime_news_screening     — every 6h: re-scan top-risk entities in news
    fincrime_retrain_layer0     — weekly Sunday 02:00 WIB: retrain Layer 0
    fincrime_drift_check        — daily 06:00 WIB: PSI drift report, alert if high
"""
from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator
except ImportError:
    # Skeleton stubs so this file imports cleanly outside Airflow.
    DAG = BashOperator = PythonOperator = None


DEFAULT_ARGS = {
    "owner": "fincrime-compliance",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["compliance@fincrime.id"],
}

# Common env: PROJECT_ROOT must point to the FinCrime checkout on the worker.
PROJECT_ROOT = "/opt/fincrime"
PY = f"{PROJECT_ROOT}/.venv312/bin/python"


# ============================================================
# 1. Refresh sanctions (daily)
# ============================================================
if DAG is not None:
    with DAG(
        "fincrime_refresh_sanctions",
        description="Pull fresh OFAC SDN + UN consolidated list, re-flag entities.",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2026, 1, 1),
        schedule="0 21 * * *",       # 21:00 UTC = 04:00 WIB
        catchup=False,
        tags=["aml", "compliance", "daily"],
    ) as dag_sanctions:
        BashOperator(
            task_id="fetch_ofac",
            bash_command=f"cd {PROJECT_ROOT} && {PY} scripts/fetch_sanctions.py --force-refresh",
        ) >> BashOperator(
            task_id="dttot_refresh",
            bash_command=f"curl -sf -X POST http://api:8000/v1/screening/dttot/refresh",
        )

    # ============================================================
    # 2. Negative news screening (every 6h)
    # ============================================================
    with DAG(
        "fincrime_news_screening",
        description="Scan Indonesian media for negative news on high-risk entities.",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2026, 1, 1),
        schedule="0 */6 * * *",
        catchup=False,
        tags=["aml", "screening"],
    ) as dag_news:
        def _scan_top_risk(**_):
            import httpx
            r = httpx.get("http://api:8000/v1/entities/top?limit=20").json()
            for e in r.get("entities", []):
                if e["score"] < 70:
                    continue
                httpx.get(f"http://api:8000/v1/screening/news/{e['entity_id']}")
        PythonOperator(task_id="scan_top_risk_entities", python_callable=_scan_top_risk)

    # ============================================================
    # 3. Weekly Layer 0 retrain
    # ============================================================
    with DAG(
        "fincrime_retrain_layer0",
        description="Retrain XGBoost risk-scoring model on latest entity data.",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2026, 1, 1),
        schedule="0 19 * * 0",       # Sun 19:00 UTC = Mon 02:00 WIB
        catchup=False,
        tags=["mlops", "training", "weekly"],
    ) as dag_retrain:
        BashOperator(
            task_id="retrain_with_mlflow",
            bash_command=f"cd {PROJECT_ROOT} && {PY} scripts/train_with_mlflow.py",
        )

    # ============================================================
    # 4. Drift check + alert (daily)
    # ============================================================
    with DAG(
        "fincrime_drift_check",
        description="Compute PSI drift between baseline & current, alert if high.",
        default_args=DEFAULT_ARGS,
        start_date=datetime(2026, 1, 1),
        schedule="0 23 * * *",       # 23:00 UTC = 06:00 WIB
        catchup=False,
        tags=["mlops", "monitoring"],
    ) as dag_drift:
        def _check_drift(**_):
            import httpx
            r = httpx.get("http://api:8000/v1/monitoring/drift").json()
            if r.get("overall_severity") == "high":
                httpx.post(
                    "http://api:8000/v1/alerts/test-broadcast",
                    params={"severity": "high",
                            "title": f"Feature drift HIGH (PSI={r['overall_psi']})"},
                )
        PythonOperator(task_id="check_drift", python_callable=_check_drift)

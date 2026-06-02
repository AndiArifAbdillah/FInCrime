"""Weekly retraining of Layer 0 + Layer 1 + Layer 2 with MLflow tracking."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from airflow import DAG
from airflow.operators.python import PythonOperator


def retrain_layer0():
    from scripts.train_with_mlflow import train_layer0_mlflow
    return train_layer0_mlflow()


def retrain_layer1():
    from scripts.train_with_mlflow import train_layer1_mlflow
    return train_layer1_mlflow()


def retrain_layer2():
    from scripts.train_with_mlflow import train_layer2_mlflow
    return train_layer2_mlflow()


def audit_retrain(**ctx):
    from src.observability import audit_log
    audit_log.record(
        event_type="model_retrained",
        actor="airflow",
        subject="all_layers",
        action="retrain",
    )


default_args = {
    "owner": "fincrime-ops",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=30),
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    "fincrime_retrain_weekly",
    description="Weekly retraining Layer 0 + 1 + 2 with MLflow tracking",
    schedule="0 3 * * 1",   # Monday 03:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["fincrime", "training", "weekly"],
) as dag:

    l0 = PythonOperator(task_id="retrain_layer0", python_callable=retrain_layer0)
    l1 = PythonOperator(task_id="retrain_layer1", python_callable=retrain_layer1)
    l2 = PythonOperator(task_id="retrain_layer2", python_callable=retrain_layer2)
    audit = PythonOperator(task_id="audit_log", python_callable=audit_retrain)
    [l0, l1, l2] >> audit

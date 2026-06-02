"""Daily refresh of OFAC + UN sanctions lists + DTTOT cross-check."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Allow `import src.*` from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


def refresh_ofac():
    from src.ingestion.sanctions_loader import (
        download_ofac_sdn, parse_ofac_sdn,
        flag_entities_against_sanctions,
    )
    import pandas as pd
    from src.common.config import settings

    sdn = download_ofac_sdn(force=True)
    entries = parse_ofac_sdn(sdn)
    print(f"[OFAC] Refreshed: {len(entries):,} entries")

    csv = settings.app_data_dir / "sample" / "entities.csv"
    if csv.exists():
        df = pd.read_csv(csv)
        new_df, stats = flag_entities_against_sanctions(df)
        new_df.to_csv(csv, index=False)
        print(f"[OFAC] Applied: matched_names={stats['matched_names']}, "
              f"matched_wallets={stats['matched_wallets']}")
    return stats if csv.exists() else {"skipped": True}


def refresh_un():
    from src.integrations.sanctions_dttot import download_un_list, parse_un_list
    p = download_un_list(force=True)
    entries = parse_un_list(p)
    print(f"[UN] {len(entries):,} entries refreshed")
    return {"total": len(entries)}


def audit_refresh(**ctx):
    from src.observability import audit_log
    audit_log.record(
        event_type="data_access",
        actor="airflow",
        subject="ofac_un_lists",
        action="refresh",
        payload={"ti": str(ctx.get("ti"))},
    )


default_args = {
    "owner": "fincrime-ops",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    "fincrime_ofac_refresh",
    description="Refresh OFAC SDN + UN Consolidated daily, apply to entities",
    schedule="0 2 * * *",   # daily 02:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["fincrime", "sanctions", "daily"],
) as dag:

    refresh_ofac_t = PythonOperator(task_id="refresh_ofac",  python_callable=refresh_ofac)
    refresh_un_t   = PythonOperator(task_id="refresh_un",    python_callable=refresh_un)
    audit_t        = PythonOperator(task_id="audit_log",     python_callable=audit_refresh)
    [refresh_ofac_t, refresh_un_t] >> audit_t

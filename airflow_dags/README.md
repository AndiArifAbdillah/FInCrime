# FinCrime — Airflow DAGs

Scheduled tasks for FinCrime production deployment.

## Setup (local Airflow)

```bash
pip install apache-airflow==2.10.3
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow_dags
export AIRFLOW__CORE__LOAD_EXAMPLES=False

airflow db init
airflow users create --username admin --password admin --firstname A --lastname B --email a@b.com --role Admin
airflow standalone   # runs scheduler + webserver
# Open http://localhost:8080
```

## DAGs included

| DAG | Schedule | What it does |
|-----|----------|--------------|
| `fincrime_ofac_refresh` | daily @ 02:00 | Re-downloads OFAC SDN + UN consolidated list, re-applies to entities |
| `fincrime_retrain_layer0` | weekly Mon @ 03:00 | Re-trains Layer 0 XGBoost on latest entities, logs to MLflow |
| `fincrime_retrain_layer1` | weekly Mon @ 03:30 | Re-trains Layer 1 IsolationForest + Autoencoder |
| `fincrime_drift_check` | every 6 hours | Computes PSI drift, alerts compliance lead if PSI > 0.25 |
| `fincrime_news_screening` | every 4 hours | Scrapes Indonesian media for negative news about flagged entities |

## Production deployment

Use **Airflow on Kubernetes** with [KubernetesExecutor](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/index.html).

For managed: AWS MWAA, GCP Composer, Astronomer Cloud.

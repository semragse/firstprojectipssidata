from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from ml.ai_forecast import build_and_save_forecast

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ai_forecast_pipeline",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 11, 17),
    schedule_interval="0 5 * * *",  # daily early morning
    catchup=False,
    tags=["forecast", "ai", "machine-learning"],
):

    forecast = PythonOperator(
        task_id="ai_forecast",
        python_callable=build_and_save_forecast,
    )

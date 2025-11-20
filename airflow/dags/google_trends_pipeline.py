"""Airflow DAG: Google Trends multi-keyword daily pipeline.

Tâches:
- extract_<keyword>_trends: extrait 12 derniers mois (daily) pour chaque mot-clé.
- merge_trends: fusionne toutes les extractions en format long et écrit Parquet dans data/processed.

Note SSL: utilisation verify=False (insecure) à cause d'environnement interceptant les certificats. Remplacer par un CA bundle si disponible.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.stats import Stats
from monitoring.alerts import task_failure_callback, task_success_callback

KEYWORDS = [
    "ChatGPT",
    "AI",
    "Machine Learning",
    "Python",
    "Data Science",
]

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": task_failure_callback,
    "on_success_callback": task_success_callback,
}

def extract_keyword(keyword: str, **context) -> str:
    safe = keyword.lower().replace(" ", "_")
    pytrends = TrendReq(hl="en-US", tz=360, requests_args={"verify": False})
    pytrends.build_payload([keyword], timeframe="today 12-m")
    df = pytrends.interest_over_time()
    if df.empty:
        raise ValueError(f"Aucune donnée pour {keyword}")
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    df.index.name = "date"
    start_date = df.index.min().strftime("%Y%m%d")
    end_date = df.index.max().strftime("%Y%m%d")
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"google_trends_{safe}_daily_{start_date}_{end_date}.csv"
    out_path = out_dir / filename
    # Pour un seul mot-clé, DataFrame a une seule colonne -> écrire directement
    df.to_csv(out_path)
    Stats.incr("trends_extract_success")
    return str(out_path)

def merge_trends(**context) -> str:
    ti = context["ti"]
    frames = []
    for keyword in KEYWORDS:
        safe = keyword.lower().replace(" ", "_")
        task_id = f"extract_{safe}_trends"
        path = ti.xcom_pull(task_ids=task_id)
        if not path:
            continue
        df_raw = pd.read_csv(path)
        # Première colonne: date, seconde: valeur du mot-clé
        value_col = [c for c in df_raw.columns if c != "date"][0]
        df_long = df_raw.rename(columns={value_col: "value"})
        df_long["keyword"] = safe
        frames.append(df_long)
    if not frames:
        raise ValueError("Aucun fichier à fusionner.")
    full = pd.concat(frames, ignore_index=True)
    full["ingestion_ts"] = datetime.utcnow().isoformat()
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    logical_date = context["ds"].replace("-", "")
    out_file = processed_dir / f"google_trends_all_daily_{logical_date}.parquet"
    try:
        full.to_parquet(out_file)
        Stats.incr("trends_merge_parquet_success")
        return str(out_file)
    except Exception:
        csv_fallback = processed_dir / f"google_trends_all_daily_{logical_date}.csv"
        full.to_csv(csv_fallback, index=False)
        Stats.incr("trends_merge_csv_fallback")
        return str(csv_fallback)

with DAG(
    dag_id="google_trends_pipeline",
    default_args=DEFAULT_ARGS,
    schedule_interval="@daily",
    start_date=datetime(2024, 11, 17),
    catchup=False,
    tags=["google_trends", "data"],
) as dag:

    extract_tasks = []
    for kw in KEYWORDS:
        safe = kw.lower().replace(" ", "_")
        t = PythonOperator(
            task_id=f"extract_{safe}_trends",
            python_callable=extract_keyword,
            op_kwargs={"keyword": kw},
        )
        extract_tasks.append(t)

    merge = PythonOperator(
        task_id="merge_trends",
        python_callable=merge_trends,
    )

    extract_tasks >> merge

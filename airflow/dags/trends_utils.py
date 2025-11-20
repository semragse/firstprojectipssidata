"""Utility functions for Google Trends extraction/merge (sans import Airflow)."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import pandas as pd
from pytrends.request import TrendReq

KEYWORDS = [
    "Airflow",
    "Databricks",
    "Collibra",
    "Data engineering",
    "Data quality",
]

def extract_keyword(keyword: str) -> str:
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
    df.to_csv(out_path)
    return str(out_path)

def merge_paths(paths: list[str], logical_date: str = None) -> str:
    frames = []
    for p in paths:
        df_raw = pd.read_csv(p)
        value_col = [c for c in df_raw.columns if c != "date"][0]
        keyword = p.split("google_trends_")[1].split("_daily_")[0]
        df_long = df_raw.rename(columns={value_col: "value"})
        df_long["keyword"] = keyword
        frames.append(df_long)
    full = pd.concat(frames, ignore_index=True)
    full["ingestion_ts"] = datetime.utcnow().isoformat()
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    logical_date = logical_date or datetime.utcnow().strftime("%Y%m%d")
    out_file = processed_dir / f"google_trends_all_daily_{logical_date}.parquet"
    try:
        full.to_parquet(out_file)
        return str(out_file)
    except Exception:
        csv_fallback = processed_dir / f"google_trends_all_daily_{logical_date}.csv"
        full.to_csv(csv_fallback, index=False)
        return str(csv_fallback)

"""Transformations analytics Google Trends (12 derniers mois)

Génère des fichiers dans data/processed/analytics/:
- chatgpt_evolution.csv : évolution et stats ChatGPT
- ai_peaks.csv : pics d'intérêt pour AI
- python_top_countries.csv : top pays pour Python
- machine_learning_fr_us.csv : comparaison FR vs US pour 'Machine Learning'
- data_science_peaks.csv : détection de pics pour 'Data Science'

Utilise pytrends avec verify=False (SSL intercept). Ajouter --secure pour activer la vérification.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
from pytrends.request import TrendReq
import argparse
import statistics

OUTPUT_DIR = Path("data/processed/analytics")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TIMEFRAME = "today 12-m"

@dataclass
class FetchConfig:
    verify: bool | str = False  # False par défaut pour contourner cert intercept
    hl: str = "en-US"
    tz: int = 360

# --------------------- Fetch helpers --------------------- #

def make_client(cfg: FetchConfig) -> TrendReq:
    return TrendReq(hl=cfg.hl, tz=cfg.tz, requests_args={"verify": cfg.verify})

def fetch_time_series(client: TrendReq, keyword: str, geo: str | None = None) -> pd.DataFrame:
    client.build_payload([keyword], timeframe=TIMEFRAME, geo=geo)
    df = client.interest_over_time()
    if df.empty:
        raise ValueError(f"Aucune donnée retournée pour {keyword} (geo={geo}).")
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    df.index.name = "date"
    return df.rename(columns={keyword: "value"}).reset_index()

def fetch_region(client: TrendReq, keyword: str, resolution: str = "COUNTRY") -> pd.DataFrame:
    client.build_payload([keyword], timeframe=TIMEFRAME)
    df = client.interest_by_region(resolution=resolution, inc_low_vol=True, inc_geo_code=False)
    if df.empty:
        raise ValueError(f"Aucune donnée région pour {keyword}.")
    return df.sort_values(keyword, ascending=False).reset_index().rename(columns={"geoName": "region", keyword: "value"})

# --------------------- Analytics --------------------- #

def airflow_evolution(df: pd.DataFrame, keyword: str = "airflow") -> pd.DataFrame:
    df_sorted = df.sort_values("date")
    first_val = df_sorted.iloc[0]["value"]
    last_val = df_sorted.iloc[-1]["value"]
    pct_change = (last_val - first_val) / first_val * 100 if first_val else None
    mean_val = df_sorted["value"].mean()
    median_val = statistics.median(df_sorted["value"])
    rolling_4w = df_sorted.set_index("date")["value"].rolling("28D").mean().reset_index().rename(columns={"value": "rolling_28d_mean"})
    summary = pd.DataFrame([
        {
            "first_value": first_val,
            "last_value": last_val,
            "pct_change": round(pct_change, 2) if pct_change is not None else None,
            "mean": round(mean_val, 2),
            "median": median_val,
            "n_points": len(df_sorted),
        }
    ])
    out_stats = OUTPUT_DIR / f"{keyword}_evolution.csv"
    summary.to_csv(out_stats, index=False)
    out_series = OUTPUT_DIR / f"{keyword}_evolution_series.csv"
    pd.merge(df_sorted, rolling_4w, on="date", how="left").to_csv(out_series, index=False)
    return summary

def detect_peaks(df: pd.DataFrame, window: int = 4, z_threshold: float = 1.5) -> pd.DataFrame:
    s = df.sort_values("date").set_index("date")["value"]
    roll_mean = s.rolling(window).mean()
    roll_std = s.rolling(window).std()
    z_scores = (s - roll_mean) / roll_std
    peaks = s[(z_scores > z_threshold)].reset_index().rename(columns={"value": "peak_value"})
    peaks["z_score"] = z_scores[peaks.index].values
    return peaks

def databricks_peaks(df: pd.DataFrame, keyword: str = "databricks") -> pd.DataFrame:
    peaks = detect_peaks(df, window=4, z_threshold=1.5)
    top = peaks.sort_values("peak_value", ascending=False).head(10)
    out_file = OUTPUT_DIR / f"{keyword}_peaks.csv"
    top.to_csv(out_file, index=False)
    return top

def collibra_top_countries(df_region: pd.DataFrame, keyword: str = "collibra", top_n: int = 10) -> pd.DataFrame:
    top = df_region.head(top_n)
    out_file = OUTPUT_DIR / f"{keyword}_top_countries.csv"
    top.to_csv(out_file, index=False)
    return top

def data_engineering_fr_vs_us(fr_df: pd.DataFrame, us_df: pd.DataFrame, keyword: str = "data_engineering") -> pd.DataFrame:
    fr_df = fr_df.rename(columns={"value": "fr_value"})
    us_df = us_df.rename(columns={"value": "us_value"})
    merged = pd.merge(fr_df, us_df, on="date", how="inner")
    merged["diff"] = merged["fr_value"] - merged["us_value"]
    out_file = OUTPUT_DIR / f"{keyword}_fr_us.csv"
    merged.to_csv(out_file, index=False)
    return merged

def data_quality_peaks(df: pd.DataFrame, keyword: str = "data_quality") -> pd.DataFrame:
    peaks = detect_peaks(df, window=4, z_threshold=1.5)
    out_file = OUTPUT_DIR / f"{keyword}_peaks.csv"
    peaks.to_csv(out_file, index=False)
    return peaks

# --------------------- Main orchestration --------------------- #

def run_all(cfg: FetchConfig) -> None:
    client = make_client(cfg)
    # ChatGPT evolution
    chatgpt_df = fetch_time_series(client, "ChatGPT")
    chatgpt_stats = airflow_evolution(chatgpt_df, "chatgpt")

    # AI peaks
    ai_df = fetch_time_series(client, "AI")
    ai_peak_df = databricks_peaks(ai_df, "ai")

    # Python top countries
    python_region_df = fetch_region(client, "Python")
    python_top = collibra_top_countries(python_region_df, "python")

    # Machine Learning FR vs US
    fr_df = fetch_time_series(client, "Machine Learning", geo="FR")
    us_df = fetch_time_series(client, "Machine Learning", geo="US")
    ml_fr_us_df = data_engineering_fr_vs_us(fr_df, us_df, "machine_learning")

    # Data Science peaks
    data_science_df = fetch_time_series(client, "Data Science")
    ds_peaks_df = data_quality_peaks(data_science_df, "data_science")

    print("[DONE] Transformations terminées")
    for name, df in [
        ("chatgpt_evolution", chatgpt_stats),
        ("ai_peaks", ai_peak_df),
        ("python_top_countries", python_top),
        ("machine_learning_fr_us", ml_fr_us_df.head()),
        ("data_science_peaks", ds_peaks_df.head()),
    ]:
        print(f"--- {name} ---")
        print(df.head())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analytics Google Trends 12 mois")
    parser.add_argument("--secure", action="store_true", help="Activer vérification SSL")
    parser.add_argument("--ca-bundle", help="Chemin bundle CA")
    args = parser.parse_args()
    verify: bool | str
    if args.secure:
        verify = True
    elif args.ca_bundle:
        verify = args.ca_bundle
    else:
        verify = False
    cfg = FetchConfig(verify=verify)
    run_all(cfg)

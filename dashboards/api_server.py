from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

from ml.databricks_forecast import sarimax_forecast, load_latest_databricks_series, FORECAST_HORIZON

app = FastAPI(title="DataLakeVendredi Dashboard API")
ANALYTICS_DIR = Path("data/processed/analytics")

# Utility loaders

def load_csv(name: str) -> pd.DataFrame:
    path = ANALYTICS_DIR / name
    if not path.exists():
        raise FileNotFoundError(name)
    return pd.read_csv(path)

@app.get("/")
def root():
    return {"service": "dashboard-api", "time": datetime.utcnow().isoformat()}

@app.get("/airflow/evolution")
def airflow_evolution():
    try:
        df = load_csv("airflow_evolution_series.csv")
        return [
            {
                "date": r.date,
                "value": r.value,
                "rolling_28d_mean": r.rolling_28d_mean
            } for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="airflow evolution not found")

@app.get("/databricks/peaks")
def databricks_peaks():
    try:
        df = load_csv("databricks_peaks.csv")
        if df.empty:
            return []
        return [
            {
                "date": r.date,
                "peak_value": r.peak_value,
                "z_score": r.z_score
            } for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="databricks peaks not found")

@app.get("/collibra/map")
def collibra_map():
    try:
        df = load_csv("collibra_top_countries.csv")
        return [
            {"region": r.region, "value": r.value} for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="collibra map not found")

@app.get("/data-engineering/fr-vs-us")
def data_engineering_fr_us():
    try:
        df = load_csv("data_engineering_fr_us.csv")
        return [
            {
                "date": r.date,
                "fr_value": r.fr_value,
                "us_value": r.us_value,
                "diff": r.diff
            } for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="fr vs us not found")

@app.get("/data-quality/events-correlation")
def data_quality_events():
    path = ANALYTICS_DIR / "data_quality_event_correlation.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="event correlation not found")
    return json.loads(path.read_text())

@app.get("/databricks/forecast")
def databricks_forecast():
    try:
        df = load_latest_databricks_series()
        fc = sarimax_forecast(df)
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "horizon_days": FORECAST_HORIZON,
            "points": [
                {
                    "date": r.date.strftime('%Y-%m-%d'),
                    "forecast": r.forecast,
                    "lower80": r.lower80,
                    "upper80": r.upper80
                } for r in fc.itertuples()
            ]
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="databricks raw series not found")

@app.get("/health")
def health():
    return {"status": "ok"}

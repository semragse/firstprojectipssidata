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

@app.get("/chatgpt/evolution")
def chatgpt_evolution():
    try:
        df = load_csv("chatgpt_evolution_series.csv")
        return [
            {
                "date": r.date,
                "value": r.value,
                "rolling_28d_mean": r.rolling_28d_mean
            } for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="chatgpt evolution not found")

@app.get("/ai/peaks")
def ai_peaks():
    try:
        df = load_csv("ai_peaks.csv")
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
        raise HTTPException(status_code=404, detail="ai peaks not found")

@app.get("/python/map")
def python_map():
    try:
        df = load_csv("python_top_countries.csv")
        return [
            {"region": r.region, "value": r.value} for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="python map not found")

@app.get("/machine-learning/fr-vs-us")
def machine_learning_fr_us():
    try:
        df = load_csv("machine_learning_fr_us.csv")
        return [
            {
                "date": r.date,
                "fr_value": r.fr_value,
                "us_value": r.us_value,
                "diff": r.diff
            } for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="machine learning fr vs us not found")

@app.get("/data-science/events-correlation")
def data_science_events():
    path = ANALYTICS_DIR / "data_quality_event_correlation.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="event correlation not found")
    return json.loads(path.read_text())

@app.get("/ai/forecast")
def ai_forecast():
    try:
        df = load_csv("ai_forecast.csv")
        return [
            {
                "date": r.date,
                "forecast": r.forecast,
                "lower80": r.lower80,
                "upper80": r.upper80
            } for r in df.itertuples()
        ]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="ai forecast not found")

@app.get("/health")
def health():
    return {"status": "ok"}

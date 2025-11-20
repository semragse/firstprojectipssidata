import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
except Exception:
    SARIMAX = None

DATA_RAW_DIR = Path("data/raw")
OUTPUT_PATH = Path("data/processed/analytics/databricks_forecast.csv")

FORECAST_HORIZON = 30  # days


def load_latest_databricks_series() -> pd.DataFrame:
    files = sorted(DATA_RAW_DIR.glob("google_trends_databricks_daily_*.csv"))
    if not files:
        raise FileNotFoundError("No Databricks daily raw file found")
    latest = files[-1]
    df = pd.read_csv(latest)
    # Expect columns: date, Databricks
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return df[['date', 'Databricks']].rename(columns={'Databricks': 'value'})


def naive_forecast(df: pd.DataFrame) -> pd.DataFrame:
    # Seasonal naive weekly (repeat last 7) if length >= 7 else simple mean
    last_values = df['value'].tail(7).tolist()
    mean_val = df['value'].mean()
    start_date = df['date'].max() + timedelta(days=1)
    rows = []
    for i in range(FORECAST_HORIZON):
        d = start_date + timedelta(days=i)
        if len(last_values) == 7:
            val = last_values[i % 7]
        else:
            val = mean_val
        rows.append({'date': d, 'forecast': val})
    return pd.DataFrame(rows)


def sarimax_forecast(df: pd.DataFrame) -> pd.DataFrame:
    # Simple SARIMAX, fallback to naive if fails
    try:
        if SARIMAX is None:
            raise RuntimeError("statsmodels not available")
        series = df.set_index('date')['value']
        # Basic differencing to handle potential trend
        model = SARIMAX(series, order=(1,1,1), seasonal_order=(1,0,1,7), enforce_stationarity=False, enforce_invertibility=False)
        res = model.fit(disp=False)
        future_index = [series.index.max() + timedelta(days=i) for i in range(1, FORECAST_HORIZON+1)]
        forecast = res.get_forecast(steps=FORECAST_HORIZON)
        mean = forecast.predicted_mean
        conf_int = forecast.conf_int(alpha=0.2)  # 80% interval
        out_rows = []
        for d in future_index:
            val = float(mean.loc[d])
            lower = float(conf_int.loc[d][0])
            upper = float(conf_int.loc[d][1])
            out_rows.append({'date': d, 'forecast': val, 'lower80': lower, 'upper80': upper})
        return pd.DataFrame(out_rows)
    except Exception:
        nf = naive_forecast(df)
        nf['lower80'] = nf['forecast'] * 0.9
        nf['upper80'] = nf['forecast'] * 1.1
        return nf


def build_and_save_forecast() -> str:
    df = load_latest_databricks_series()
    fc = sarimax_forecast(df)
    fc.to_csv(OUTPUT_PATH, index=False)
    return str(OUTPUT_PATH)


def as_json() -> str:
    df = load_latest_databricks_series()
    fc = sarimax_forecast(df)
    return json.dumps({
        'generated_at': datetime.utcnow().isoformat(),
        'horizon_days': FORECAST_HORIZON,
        'points': [
            {
                'date': r['date'].strftime('%Y-%m-%d'),
                'forecast': r['forecast'],
                'lower80': r['lower80'],
                'upper80': r['upper80']
            } for _, r in fc.iterrows()
        ]
    })

if __name__ == '__main__':
    path = build_and_save_forecast()
    print(f"Forecast saved to {path}")

"""Correlation between Data Quality Google Trends peaks and external events.

Outputs:
- data/processed/analytics/data_quality_peak_event_matches.csv
- data/processed/analytics/data_quality_event_correlation.json

Weighted Score (optional):
    score = peak_value * importance / (1 + abs(delta_days))
This emphasizes high peaks & important events occurring close to the peak date.

Usage (example):
python airflow/dags/correlation_events.py --events-path data/processed/analytics/events_mock.csv --recompute-peaks --z-threshold 1.2 --window-days 10 --compute-score
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

try:
    from pytrends.request import TrendReq  # optional if recompute
except ImportError:
    TrendReq = None  # type: ignore

ANALYTICS_DIR = Path("data/processed/analytics")
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
PEAKS_FILE = ANALYTICS_DIR / "data_quality_peaks.csv"
MATCHES_FILE = ANALYTICS_DIR / "data_quality_peak_event_matches.csv"
SUMMARY_FILE = ANALYTICS_DIR / "data_quality_event_correlation.json"

@dataclass
class Config:
    events_path: Path
    window_days: int = 3
    min_importance: int = 1
    strict: bool = False
    recompute_peaks: bool = False
    z_threshold: float = 1.5
    verify: bool | str = False
    compute_score: bool = False

# ---------------- Peak recomputation ---------------- #

def recompute_peaks(z_threshold: float, verify: bool | str) -> pd.DataFrame:
    if TrendReq is None:
        raise RuntimeError("pytrends non installé: impossible de recomputer les pics.")
    client = TrendReq(hl="en-US", tz=360, requests_args={"verify": verify})
    client.build_payload(["Data quality"], timeframe="today 12-m")
    df = client.interest_over_time()
    if df.empty:
        raise ValueError("Aucune donnée Data quality pour recompute.")
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    df.index.name = "date"
    s = df["Data quality"].rename("value")
    series = s.to_frame().reset_index()
    # Rolling stats
    s_sorted = series.sort_values("date")
    s_idx = s_sorted.set_index("date")["value"]
    roll_mean = s_idx.rolling(4).mean()
    roll_std = s_idx.rolling(4).std()
    z_scores = (s_idx - roll_mean) / roll_std
    peaks = s_idx[(z_scores > z_threshold)].reset_index().rename(columns={"value": "peak_value"})
    peaks["z_score"] = z_scores[peaks.index].values
    peaks.to_csv(PEAKS_FILE, index=False)
    return peaks

# ---------------- Matching logic ---------------- #

def load_peaks(recompute: bool, z_threshold: float, verify: bool | str) -> pd.DataFrame:
    if recompute or not PEAKS_FILE.exists():
        return recompute_peaks(z_threshold, verify)
    return pd.read_csv(PEAKS_FILE, parse_dates=["date"]) if PEAKS_FILE.exists() else pd.DataFrame()

def load_events(path: Path, min_importance: int) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["event_date"], dtype={"importance": "int"})
    df = df[df["importance"] >= min_importance].copy()
    return df

def match_peaks_events(peaks: pd.DataFrame, events: pd.DataFrame, window_days: int, strict: bool, compute_score: bool) -> pd.DataFrame:
    if peaks.empty:
        return pd.DataFrame(columns=["date", "peak_value", "z_score", "event_date", "event_name", "event_type", "importance", "delta_days", "match_type"])
    events_indexed = events.set_index("event_date")
    matches_rows: List[Dict[str, Any]] = []
    for _, peak in peaks.iterrows():
        peak_date = pd.to_datetime(peak["date"]).normalize()
        start = peak_date - timedelta(days=window_days)
        end = peak_date + timedelta(days=window_days)
        if strict:
            window_events = events_indexed.loc[[peak_date]] if peak_date in events_indexed.index else pd.DataFrame(columns=events_indexed.columns)
        else:
            window_events = events_indexed.loc[start:end] if not events_indexed.index.empty else pd.DataFrame(columns=events_indexed.columns)
        if window_events.empty:
            continue
        for ev_date, ev_row in window_events.iterrows():
            delta = (ev_date - peak_date).days
            if delta == 0:
                mtype = "exact"
            elif delta < 0:
                mtype = "before"
            else:
                mtype = "after"
            score = None
            if compute_score:
                peak_value = peak.get("peak_value") or 0
                importance = ev_row.get("importance") or 0
                score = (peak_value * importance) / (1 + abs(delta))
            matches_rows.append({
                "date": peak_date.date().isoformat(),
                "peak_value": peak.get("peak_value"),
                "z_score": peak.get("z_score"),
                "event_date": ev_date.date().isoformat(),
                "event_name": ev_row.get("event_name"),
                "event_type": ev_row.get("event_type"),
                "importance": ev_row.get("importance"),
                "delta_days": delta,
                "match_type": mtype,
                "score": score,
            })
    return pd.DataFrame(matches_rows)

# ---------------- Metrics ---------------- #

def build_metrics(peaks: pd.DataFrame, matches: pd.DataFrame) -> Dict[str, Any]:
    total_peaks = len(peaks)
    matched_peak_dates = set(matches["date"]) if not matches.empty else set()
    matched_peaks = len(matched_peak_dates)
    match_rate = matched_peaks / total_peaks if total_peaks else 0
    events_per_matched_peak = matches.shape[0] / matched_peaks if matched_peaks else 0
    distribution = matches["delta_days"].value_counts().to_dict() if not matches.empty else {}
    top_event_types = matches["event_type"].value_counts().head(10).to_dict() if not matches.empty else {}
    mean_importance = matches["importance"].mean() if not matches.empty else 0
    mean_score = matches["score"].mean() if (not matches.empty and "score" in matches.columns) else 0
    return {
        "total_peaks": total_peaks,
        "matched_peaks": matched_peaks,
        "match_rate": round(match_rate, 3),
        "events_per_matched_peak": round(events_per_matched_peak, 2),
        "distribution_lead_lag": distribution,
        "top_event_types": top_event_types,
        "mean_importance": round(mean_importance, 2),
        "mean_score": round(mean_score, 2),
    }

# ---------------- Main ---------------- #

def main():
    parser = argparse.ArgumentParser(description="Corrélation pics 'Data quality' vs événements externes")
    parser.add_argument("--events-path", required=True, help="Chemin fichier CSV événements")
    parser.add_argument("--window-days", type=int, default=3)
    parser.add_argument("--min-importance", type=int, default=1)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--recompute-peaks", action="store_true")
    parser.add_argument("--z-threshold", type=float, default=1.5)
    parser.add_argument("--secure", action="store_true")
    parser.add_argument("--ca-bundle")
    parser.add_argument("--output-dir", default=str(ANALYTICS_DIR))
    parser.add_argument("--compute-score", action="store_true", help="Calcule score pondéré pour chaque correspondance.")
    args = parser.parse_args()

    verify: bool | str
    if args.secure:
        verify = True
    elif args.ca_bundle:
        verify = args.ca_bundle
    else:
        verify = False

    cfg = Config(
        events_path=Path(args.events_path),
        window_days=args.window_days,
        min_importance=args.min_importance,
        strict=args.strict,
        recompute_peaks=args.recompute_peaks,
        z_threshold=args.z_threshold,
        verify=verify,
        compute_score=args.compute_score,
    )

    peaks = load_peaks(cfg.recompute_peaks, cfg.z_threshold, cfg.verify)
    # Parse dates if recompute returned naive index
    if "date" in peaks.columns:
        peaks["date"] = pd.to_datetime(peaks["date"]) if not pd.api.types.is_datetime64_any_dtype(peaks["date"]) else peaks["date"]

    events = load_events(cfg.events_path, cfg.min_importance)
    matches = match_peaks_events(peaks, events, cfg.window_days, cfg.strict, cfg.compute_score)
    metrics = build_metrics(peaks, matches)

    # Save outputs
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    matches.to_csv(out_dir / MATCHES_FILE.name, index=False)
    with open(out_dir / SUMMARY_FILE.name, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.utcnow().isoformat(),
            "parameters": {
                "window_days": cfg.window_days,
                "z_threshold": cfg.z_threshold,
                "min_importance": cfg.min_importance,
                "strict": cfg.strict,
                "compute_score": cfg.compute_score,
            },
            "metrics": metrics,
            "top_matches": matches.sort_values("score", ascending=False).head(10).to_dict(orient="records") if (cfg.compute_score and not matches.empty) else [],
            "sample_matches": matches.head(10).to_dict(orient="records"),
        }, f, ensure_ascii=False, indent=2)

    print("[DONE] Corrélation générée")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

"""Correlation between 'Data quality' Google Trends peaks and multiple data quality tools.

Outputs:
- data/processed/analytics/data_quality_tool_peak_matches.csv
- data/processed/analytics/data_quality_tools_correlation.json

Usage example:
python airflow/dags/correlation_tools.py --tools Collibra Talend "Great Expectations" --window-days 7 --z-threshold 1.5 --compute-score --max-lag 30
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None  # type: ignore

ANALYTICS_DIR = Path("data/processed/analytics")
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
DQ_PEAKS_FILE = ANALYTICS_DIR / "data_quality_peaks.csv"
MATCHES_FILE = ANALYTICS_DIR / "data_quality_tool_peak_matches.csv"
SUMMARY_FILE = ANALYTICS_DIR / "data_quality_tools_correlation.json"

DEFAULT_TOOLS = [
    "Collibra",
    "Talend",
    "Informatica",
    "Datafold",
    "Soda",
    "Bigeye",
    # Omitted some heavier / less common terms by default to reduce rate-limit risk.
]

@dataclass
class Config:
    tools: List[str]
    window_days: int = 7
    z_threshold: float = 1.5
    rolling_window: int = 4
    verify: bool | str = False
    compute_score: bool = False
    max_lag: int = 30
    min_tool_value: int = 0
    recompute_dq_peaks: bool = False
    recompute_tool_peaks: bool = False

# ---------------- Fetch helpers ---------------- #

def make_client(cfg: Config) -> Any:
    if TrendReq is None:
        raise RuntimeError("pytrends non installé")
    return TrendReq(hl="en-US", tz=360, requests_args={"verify": cfg.verify})

def fetch_series(client: Any, keywords: List[str], timeframe: str = "today 12-m") -> pd.DataFrame:
    """Fetch a batch of keywords. Returns DataFrame with date index reset.

    If one keyword yields no data, Google Trends typically still returns columns; we rely on emptiness check.
    """
    client.build_payload(keywords, timeframe=timeframe)
    df = client.interest_over_time()
    if df.empty:
        # Provide empty frame with date for downstream clarity
        return pd.DataFrame(columns=["date", *keywords])
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    df.index.name = "date"
    return df.reset_index()

# ---------------- Peak detection ---------------- #

def detect_peaks(series: pd.Series, rolling_window: int, z_threshold: float) -> pd.DataFrame:
    s = series.sort_index()
    roll_mean = s.rolling(rolling_window).mean()
    roll_std = s.rolling(rolling_window).std()
    z_scores = (s - roll_mean) / roll_std
    mask = z_scores > z_threshold
    peaks = s[mask]
    out = peaks.reset_index().rename(columns={series.name: "peak_value"})
    out["z_score"] = z_scores[mask].values
    return out

def load_or_compute_dq_peaks(cfg: Config, client: Any) -> pd.DataFrame:
    if not DQ_PEAKS_FILE.exists() or cfg.recompute_dq_peaks:
        dq_df = fetch_series(client, ["Data quality"])  # two columns: date, Data quality
        dq_df["date"] = pd.to_datetime(dq_df["date"])
        peaks = detect_peaks(dq_df.set_index("date")["Data quality"], cfg.rolling_window, cfg.z_threshold)
        peaks.to_csv(DQ_PEAKS_FILE, index=False)
        return peaks
    return pd.read_csv(DQ_PEAKS_FILE, parse_dates=["date"])

# ---------------- Tool peak computation ---------------- #

def compute_tool_peaks(cfg: Config, client: Any) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], List[str]]:
    """Fetch each tool separately to isolate failures and skip problematic keywords.

    Returns:
        long_df: date, tool, value rows for all successful tools
        peaks_map: mapping tool -> peaks dataframe
        skipped: list of tool names skipped due to empty/no data
    """
    peaks_map: Dict[str, pd.DataFrame] = {}
    long_rows = []
    skipped: List[str] = []
    for tool in cfg.tools:
        try:
            batch = fetch_series(client, [tool])
        except Exception as e:  # network or other error
            print(f"[WARN] Echec récupération '{tool}': {e}")
            skipped.append(tool)
            continue
        if batch.empty or tool not in batch.columns:
            print(f"[WARN] Données vides pour '{tool}', outil ignoré.")
            skipped.append(tool)
            continue
        batch["date"] = pd.to_datetime(batch["date"])
        series = batch.set_index("date")[tool]
        if cfg.min_tool_value > 0:
            series = series.where(series >= cfg.min_tool_value, 0)
        peaks = detect_peaks(series, cfg.rolling_window, cfg.z_threshold)
        peaks_map[tool] = peaks
        for d, v in series.items():
            long_rows.append({"date": d, "tool": tool.lower().replace(" ", "_"), "value": v})
    long_df = pd.DataFrame(long_rows)
    return long_df, peaks_map, skipped

# ---------------- Matching logic ---------------- #

def match_dq_to_tools(cfg: Config, dq_peaks: pd.DataFrame, tool_peaks: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    matches: List[Dict[str, Any]] = []
    for _, dq in dq_peaks.iterrows():
        dq_date = dq["date"]
        for tool, peaks in tool_peaks.items():
            if peaks.empty:
                continue
            # window slice
            start = dq_date - timedelta(days=cfg.window_days)
            end = dq_date + timedelta(days=cfg.window_days)
            subset = peaks[(peaks["date"] >= start) & (peaks["date"] <= end)]
            if subset.empty:
                continue
            for _, tp in subset.iterrows():
                delta = (tp["date"] - dq_date).days
                if delta == 0:
                    mtype = "exact"
                elif delta < 0:
                    mtype = "tool_before"
                else:
                    mtype = "tool_after"
                score = None
                if cfg.compute_score:
                    dq_val = dq.get("peak_value", 0)
                    tool_val = tp.get("peak_value", 0)
                    score = (dq_val * tool_val) / (1 + abs(delta))
                matches.append({
                    "dq_peak_date": dq_date.date().isoformat(),
                    "dq_peak_value": dq.get("peak_value"),
                    "dq_z_score": dq.get("z_score"),
                    "tool": tool.lower().replace(" ", "_"),
                    "tool_peak_date": tp["date"].date().isoformat(),
                    "tool_peak_value": tp.get("peak_value"),
                    "tool_z_score": tp.get("z_score"),
                    "delta_days": delta,
                    "match_type": mtype,
                    "score": score,
                })
    return pd.DataFrame(matches)

# ---------------- Cross correlation ---------------- #

def compute_cross_correlation(cfg: Config, dq_series: pd.Series, tool_series: pd.Series) -> Dict[str, Any]:
    # Align by date intersection
    merged = pd.merge(dq_series.rename("dq"), tool_series.rename("tool"), left_index=True, right_index=True, how="inner")
    if merged.empty:
        return {"max_corr": 0, "lag_at_max": None, "corr_map": {}}
    dq_norm = (merged["dq"] - merged["dq"].mean()) / (merged["dq"].std() or 1)
    tool_norm = (merged["tool"] - merged["tool"].mean()) / (merged["tool"].std() or 1)
    corr_map = {}
    lags = range(-cfg.max_lag, cfg.max_lag + 1)
    for lag in lags:
        if lag < 0:
            shifted = tool_norm.shift(-lag)
        else:
            shifted = tool_norm.shift(lag)
        valid = shifted.dropna()
        common = dq_norm.loc[valid.index]
        if len(common) < 5:  # require minimal overlap
            continue
        corr = float(np.corrcoef(common, valid)[0, 1])
        corr_map[lag] = round(corr, 4)
    if not corr_map:
        return {"max_corr": 0, "lag_at_max": None, "corr_map": {}}
    lag_at_max = max(corr_map, key=lambda k: corr_map[k])
    return {"max_corr": corr_map[lag_at_max], "lag_at_max": lag_at_max, "corr_map": corr_map}

# ---------------- Metrics ---------------- #

def build_metrics(cfg: Config, dq_peaks: pd.DataFrame, matches: pd.DataFrame, tool_peaks: Dict[str, pd.DataFrame], all_tools_df: pd.DataFrame, skipped: List[str]) -> Dict[str, Any]:
    total_dq_peaks = len(dq_peaks)
    tool_stats = {}
    # Build per tool cross-correlation
    dq_series_full = fetch_series(make_client(cfg), ["Data quality"])["Data quality"] if cfg.recompute_dq_peaks else None
    if dq_series_full is None:
        # We reconstruct from dq peaks file? Better to refetch once.
        client = make_client(cfg)
        dq_series_full = fetch_series(client, ["Data quality"])["Data quality"]
    dq_series_full.index = fetch_series(make_client(cfg), ["Data quality"])['date'] if isinstance(dq_series_full, pd.Series) else dq_series_full.index

    # Prepare tool value series per tool
    for tool in cfg.tools:
        peaks = tool_peaks.get(tool, pd.DataFrame())
        tool_long = all_tools_df[all_tools_df["tool"] == tool.lower().replace(" ", "_")]
        tool_series = tool_long.set_index("date")["value"].sort_index()
        cc = compute_cross_correlation(cfg, dq_series_full.sort_index(), tool_series)
        subset_matches = matches[matches["tool"] == tool.lower().replace(" ", "_")]
        matched_dq_peaks = len(set(subset_matches["dq_peak_date"]))
        match_rate = matched_dq_peaks / total_dq_peaks if total_dq_peaks else 0
        mean_score = subset_matches["score"].mean() if (cfg.compute_score and not subset_matches.empty) else 0
        median_lag = subset_matches["delta_days"].median() if not subset_matches.empty else None
        lead_ratio = float((subset_matches[subset_matches["delta_days"] < 0].shape[0]) / subset_matches.shape[0]) if not subset_matches.empty else 0
        tool_stats[tool.lower().replace(" ", "_")] = {
            "matched_dq_peaks": matched_dq_peaks,
            "match_rate": round(match_rate, 3),
            "mean_score": round(mean_score, 2),
            "median_lag": median_lag,
            "lead_ratio": round(lead_ratio, 3),
            "max_corr": cc["max_corr"],
            "lag_at_max_corr": cc["lag_at_max"],
        }
    return {
        "total_dq_peaks": total_dq_peaks,
        "tools": tool_stats,
        "skipped_tools": skipped,
    }

# ---------------- Main ---------------- #

def main():
    parser = argparse.ArgumentParser(description="Corrélation Data quality vs outils de data quality")
    parser.add_argument("--tools", nargs="*", default=DEFAULT_TOOLS, help="Liste outils")
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument("--z-threshold", type=float, default=1.5)
    parser.add_argument("--rolling-window", type=int, default=4)
    parser.add_argument("--max-lag", type=int, default=30)
    parser.add_argument("--min-tool-value", type=int, default=0)
    parser.add_argument("--compute-score", action="store_true")
    parser.add_argument("--recompute-dq-peaks", action="store_true")
    parser.add_argument("--recompute-tool-peaks", action="store_true")  # placeholder (not persisted separately now)
    parser.add_argument("--secure", action="store_true")
    parser.add_argument("--ca-bundle")
    parser.add_argument("--output-dir", default=str(ANALYTICS_DIR))
    args = parser.parse_args()

    verify: bool | str
    if args.secure:
        verify = True
    elif args.ca_bundle:
        verify = args.ca_bundle
    else:
        verify = False

    cfg = Config(
        tools=args.tools,
        window_days=args.window_days,
        z_threshold=args.z_threshold,
        rolling_window=args.rolling_window,
        max_lag=args.max_lag,
        min_tool_value=args.min_tool_value,
        compute_score=args.compute_score,
        recompute_dq_peaks=args.recompute_dq_peaks,
        recompute_tool_peaks=args.recompute_tool_peaks,
        verify=verify,
    )

    client = make_client(cfg)

    dq_peaks = load_or_compute_dq_peaks(cfg, client)

    # Compute all tool peaks (single multi-fetch)
    long_df, tool_peaks_map, skipped = compute_tool_peaks(cfg, client)
    long_df.to_csv(ANALYTICS_DIR / "tools_series_long.csv", index=False)

    matches_df = match_dq_to_tools(cfg, dq_peaks, tool_peaks_map)
    metrics = build_metrics(cfg, dq_peaks, matches_df, tool_peaks_map, long_df, skipped)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    matches_df.to_csv(out_dir / MATCHES_FILE.name, index=False)

    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "parameters": {
            "tools": cfg.tools,
            "window_days": cfg.window_days,
            "z_threshold": cfg.z_threshold,
            "rolling_window": cfg.rolling_window,
            "compute_score": cfg.compute_score,
            "max_lag": cfg.max_lag,
        },
        "metrics": metrics,
        "top_matches": matches_df.sort_values("score", ascending=False).head(20).to_dict(orient="records") if (cfg.compute_score and not matches_df.empty) else [],
        "sample_matches": matches_df.head(20).to_dict(orient="records"),
    }

    with open(out_dir / SUMMARY_FILE.name, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("[DONE] Correlation tools generated")
    if skipped:
        print(f"[INFO] Outils ignorés: {', '.join(skipped)}")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

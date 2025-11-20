import argparse
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
from pytrends.request import TrendReq
import os

KEYWORDS = [
    "Airflow",
    "Databricks",
    "Collibra",
    "Data engineering",
    "Data quality",
]

def fetch_trends(keywords: List[str], timeframe: str = "today 12-m", verify: bool | str = True) -> pd.DataFrame:
    # verify peut être True/False ou chemin vers bundle CA
    requests_args = {"verify": verify}
    pytrends = TrendReq(hl="en-US", tz=360, requests_args=requests_args)
    pytrends.build_payload(keywords, timeframe=timeframe)
    df = pytrends.interest_over_time()
    if df.empty:
        raise ValueError("Aucune donnée retournée par Google Trends.")
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    df.index.name = "date"
    return df

def transform_granularity(df: pd.DataFrame, granularity: str) -> pd.DataFrame:
    if granularity == "daily":
        return df
    if granularity == "weekly":
        # Moyenne par semaine (semaine se terminant le dimanche)
        return df.resample("W").mean().dropna(how="all")
    raise ValueError("Granularité non supportée. Choisir 'daily' ou 'weekly'.")

def write_output(df: pd.DataFrame, out_dir: Path, granularity: str, formats: List[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    start_date = df.index.min().strftime("%Y%m%d")
    end_date = df.index.max().strftime("%Y%m%d")
    base_name = f"google_trends_{granularity}_{start_date}_{end_date}"
    if "csv" in formats:
        csv_path = out_dir / f"{base_name}.csv"
        df.to_csv(csv_path)
        print(f"[OK] Fichier CSV écrit: {csv_path}")
    if "parquet" in formats:
        parquet_path = out_dir / f"{base_name}.parquet"
        try:
            df.to_parquet(parquet_path)
            print(f"[OK] Fichier Parquet écrit: {parquet_path}")
        except Exception as e:
            print(f"[WARN] Echec écriture Parquet: {e}")


def main():
    parser = argparse.ArgumentParser(description="Extraction Google Trends pour mots-clés data.")
    parser.add_argument("--granularity", "-g", choices=["daily", "weekly"], default="daily", help="Granularité de sortie.")
    parser.add_argument("--format", "-f", choices=["csv", "parquet", "both"], default="both", help="Format de sortie.")
    parser.add_argument("--out", "-o", default="data/raw", help="Répertoire de sortie.")
    parser.add_argument("--timeframe", "-t", default="today 12-m", help="Fenêtre temporelle Pytrends (ex: 'today 12-m').")
    parser.add_argument("--keywords", "-k", nargs="*", default=KEYWORDS, help="Liste de mots-clés à extraire.")
    parser.add_argument("--insecure", action="store_true", help="Désactive la vérification SSL (environnement avec proxy intercept).")
    parser.add_argument("--ca-bundle", dest="ca_bundle", help="Chemin fichier CA bundle à utiliser pour requests.")

    args = parser.parse_args()

    print(f"[INFO] Extraction mots-clés: {args.keywords}")
    print(f"[INFO] Timeframe: {args.timeframe}")

    verify: bool | str
    if args.insecure:
        verify = False
    elif args.ca_bundle:
        verify = args.ca_bundle
    else:
        verify = True
    df = fetch_trends(args.keywords, timeframe=args.timeframe, verify=verify)
    df = transform_granularity(df, args.granularity)

    formats = ["csv", "parquet"] if args.format == "both" else [args.format]
    write_output(df, Path(args.out), args.granularity, formats)

    print("[DONE] Extraction terminée.")

if __name__ == "__main__":
    main()

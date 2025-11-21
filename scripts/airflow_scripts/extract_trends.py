import argparse
from datetime import datetime
from pathlib import Path
from typing import List
import time

import pandas as pd
from pytrends.request import TrendReq
from pytrends import exceptions as pytrends_exc
import os

KEYWORDS = [
    "ChatGPT",
    "AI",
    "Machine Learning",
    "Python",
    "Data Science",
]

def fetch_trends(keywords: List[str], timeframe: str = "today 12-m", verify: bool | str = True, max_retries: int = 5, base_sleep: float = 2.0) -> pd.DataFrame:
    """Récupère les séries Google Trends mot-clé par mot-clé avec logique de retry pour limiter les erreurs 429.

    Stratégie:
      - Requêtes individuelles pour chaque mot-clé pour réduire la charge.
      - Retry exponentiel sur TooManyRequestsError ou erreurs réseau transitoires.
      - Fusion sur l'index date final.
    """
    requests_args = {"verify": verify}
    pytrends = TrendReq(hl="en-US", tz=360, requests_args=requests_args)
    all_frames: List[pd.DataFrame] = []
    for kw in keywords:
        attempt = 0
        while True:
            try:
                pytrends.build_payload([kw], timeframe=timeframe)
                df_kw = pytrends.interest_over_time()
                if df_kw.empty:
                    print(f"[WARN] Données vides pour '{kw}' – colonne ignorée.")
                    break
                if "isPartial" in df_kw.columns:
                    df_kw = df_kw.drop(columns=["isPartial"])
                df_kw.index.name = "date"
                # Conserver seulement la série du mot-clé
                series = df_kw[kw].rename(kw).to_frame()
                all_frames.append(series)
                print(f"[OK] '{kw}' récupéré ({len(series)} points)")
                # Petite pause entre requêtes pour éviter 429
                time.sleep(1.0)
                break
            except pytrends_exc.TooManyRequestsError:
                attempt += 1
                if attempt >= max_retries:
                    print(f"[ERROR] Abandon '{kw}' après {attempt} tentatives (429).")
                    break
                sleep_time = base_sleep * (2 ** (attempt - 1))
                print(f"[RETRY] 429 sur '{kw}' – attente {sleep_time:.1f}s (tentative {attempt}/{max_retries})")
                time.sleep(sleep_time)
            except Exception as e:
                attempt += 1
                if attempt >= max_retries:
                    print(f"[ERROR] Abandon '{kw}' après {attempt} tentatives: {e}")
                    break
                sleep_time = base_sleep * (2 ** (attempt - 1))
                print(f"[RETRY] Erreur '{kw}': {e} – attente {sleep_time:.1f}s (tentative {attempt}/{max_retries})")
                time.sleep(sleep_time)
    if not all_frames:
        raise ValueError("Aucune donnée retournée pour les mots-clés fournis.")
    # Fusion sur l'index (outer pour inclure toutes les dates).
    merged = pd.concat(all_frames, axis=1)
    merged.index.name = "date"
    return merged

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

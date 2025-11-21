#!/usr/bin/env python3
"""
Analyse de corrélation entre ChatGPT et Data Engineering
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
import psycopg2
from scipy import stats
import json

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trends_db',
    'user': 'trends_user',
    'password': 'trends_pass'
}

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def calculate_correlation_with_lags(series1, series2, max_lag=10):
    """
    Calculate correlation with time lags
    Returns best correlation coefficient and optimal lag
    """
    correlations = []
    lags = range(-max_lag, max_lag + 1)
    
    for lag in lags:
        if lag < 0:
            # series1 leads series2
            corr = np.corrcoef(series1[:lag], series2[-lag:])[0, 1]
        elif lag > 0:
            # series2 leads series1
            corr = np.corrcoef(series1[lag:], series2[:-lag])[0, 1]
        else:
            # No lag
            corr = np.corrcoef(series1, series2)[0, 1]
        
        correlations.append((lag, corr))
    
    # Find best correlation
    best_lag, best_corr = max(correlations, key=lambda x: abs(x[1]))
    
    return best_corr, best_lag, correlations

def analyze_chatgpt_dataeng_correlation():
    """
    Analyze correlation between ChatGPT and Data Engineering trends
    """
    print("="*60)
    print("🔗 Analyse de Corrélation ChatGPT vs Data Engineering")
    print("="*60)
    
    conn = get_db_connection()
    
    # Get ChatGPT data
    query_chatgpt = """
        SELECT date, value 
        FROM trends_raw 
        WHERE keyword = 'ChatGPT' 
        ORDER BY date
    """
    df_chatgpt = pd.read_sql(query_chatgpt, conn)
    
    # Get Data Engineering data (we'll use 'Data Science' as proxy if not available)
    query_dataeng = """
        SELECT date, value 
        FROM trends_raw 
        WHERE keyword = 'Data Science' 
        ORDER BY date
    """
    df_dataeng = pd.read_sql(query_dataeng, conn)
    
    conn.close()
    
    if len(df_chatgpt) == 0 or len(df_dataeng) == 0:
        print("❌ Données insuffisantes pour l'analyse")
        return
    
    print(f"\n📊 Données collectées:")
    print(f"   ChatGPT: {len(df_chatgpt)} points")
    print(f"   Data Science: {len(df_dataeng)} points")
    
    # Merge on date
    df_merged = pd.merge(df_chatgpt, df_dataeng, on='date', suffixes=('_chatgpt', '_dataeng'))
    
    print(f"   Points communs: {len(df_merged)}")
    
    # Basic correlation (no lag)
    basic_corr = df_merged['value_chatgpt'].corr(df_merged['value_dataeng'])
    print(f"\n🔢 Corrélation de base (sans décalage): {basic_corr:.3f}")
    
    # Correlation with lags
    print(f"\n⏱️  Analyse avec décalages temporels (±10 semaines)...")
    best_corr, best_lag, all_correlations = calculate_correlation_with_lags(
        df_merged['value_chatgpt'].values,
        df_merged['value_dataeng'].values,
        max_lag=10
    )
    
    print(f"   Meilleure corrélation: {best_corr:.3f}")
    print(f"   Décalage optimal: {best_lag} semaines")
    
    if best_lag < 0:
        print(f"   → ChatGPT mène de {abs(best_lag)} semaines")
    elif best_lag > 0:
        print(f"   → Data Science mène de {best_lag} semaines")
    else:
        print(f"   → Évolution simultanée")
    
    # Statistical significance
    _, p_value = stats.pearsonr(df_merged['value_chatgpt'], df_merged['value_dataeng'])
    print(f"\n📈 Significativité statistique:")
    print(f"   p-value: {p_value:.4f}")
    if p_value < 0.05:
        print(f"   ✅ Corrélation statistiquement significative (p < 0.05)")
    else:
        print(f"   ⚠️  Corrélation non significative (p >= 0.05)")
    
    # Growth rates
    chatgpt_growth = ((df_merged['value_chatgpt'].iloc[-1] - df_merged['value_chatgpt'].iloc[0]) / 
                      df_merged['value_chatgpt'].iloc[0] * 100)
    dataeng_growth = ((df_merged['value_dataeng'].iloc[-1] - df_merged['value_dataeng'].iloc[0]) / 
                      df_merged['value_dataeng'].iloc[0] * 100)
    
    print(f"\n📊 Taux de croissance (période complète):")
    print(f"   ChatGPT: {chatgpt_growth:+.1f}%")
    print(f"   Data Science: {dataeng_growth:+.1f}%")
    
    # Interpretation
    print(f"\n🎯 Interprétation:")
    if abs(best_corr) > 0.7:
        strength = "forte"
    elif abs(best_corr) > 0.4:
        strength = "modérée"
    else:
        strength = "faible"
    
    direction = "positive" if best_corr > 0 else "négative"
    
    print(f"   Corrélation {strength} {direction} ({best_corr:.3f})")
    
    if best_corr > 0.7:
        print(f"   → Les deux tendances évoluent fortement ensemble")
        print(f"   → L'essor de ChatGPT est lié à l'intérêt pour la Data Science")
    elif best_corr > 0:
        print(f"   → Les tendances évoluent dans le même sens")
    else:
        print(f"   → Les tendances évoluent de manière inversée")
    
    # Save results
    results = {
        "analysis_date": datetime.now().isoformat(),
        "keywords": {
            "keyword1": "ChatGPT",
            "keyword2": "Data Science"
        },
        "data_points": {
            "chatgpt": len(df_chatgpt),
            "data_science": len(df_dataeng),
            "common": len(df_merged)
        },
        "correlation": {
            "basic": float(basic_corr),
            "best": float(best_corr),
            "optimal_lag_weeks": int(best_lag),
            "p_value": float(p_value),
            "significant": bool(p_value < 0.05)
        },
        "growth_rates": {
            "chatgpt_percent": float(chatgpt_growth),
            "data_science_percent": float(dataeng_growth)
        },
        "interpretation": {
            "strength": strength,
            "direction": direction,
            "lag_interpretation": (
                f"ChatGPT mène de {abs(best_lag)} semaines" if best_lag < 0 else
                f"Data Science mène de {best_lag} semaines" if best_lag > 0 else
                "Évolution simultanée"
            )
        },
        "all_lags": [{"lag": int(lag), "correlation": float(corr)} for lag, corr in all_correlations]
    }
    
    # Save to file
    output_file = 'data/processed/analytics/chatgpt_dataeng_correlation.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés: {output_file}")
    
    # Create SQL table for correlation results
    print(f"\n📝 Création de la table SQL...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keyword_correlations (
            id SERIAL PRIMARY KEY,
            keyword1 VARCHAR(100),
            keyword2 VARCHAR(100),
            correlation_coefficient DECIMAL,
            optimal_lag_weeks INTEGER,
            p_value DECIMAL,
            is_significant BOOLEAN,
            analysis_date TIMESTAMP DEFAULT NOW()
        )
    """)
    
    cursor.execute("""
        INSERT INTO keyword_correlations 
        (keyword1, keyword2, correlation_coefficient, optimal_lag_weeks, p_value, is_significant)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        'ChatGPT',
        'Data Science',
        float(best_corr),
        int(best_lag),
        float(p_value),
        bool(p_value < 0.05)
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"   ✅ Table 'keyword_correlations' créée/mise à jour")
    
    print(f"\n{'='*60}")
    print(f"✅ Analyse de corrélation terminée!")
    print(f"{'='*60}")

if __name__ == "__main__":
    analyze_chatgpt_dataeng_correlation()

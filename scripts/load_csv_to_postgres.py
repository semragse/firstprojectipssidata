#!/usr/bin/env python3
"""
Load existing CSV data from data/ folder into PostgreSQL
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Database connection parameters
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

def load_raw_trends():
    """Load raw trends data from CSV"""
    print("📂 Loading raw trends data...")
    
    csv_path = 'data/raw/google_trends_daily_20241120_20251120.csv'
    
    if not os.path.exists(csv_path):
        print(f"   ⚠️  File not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   Found {len(df)} rows in raw data")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Prepare records for insertion
    records = []
    for _, row in df.iterrows():
        date = pd.to_datetime(row['date']).date()
        
        # Insert each keyword as a separate record
        for col in df.columns:
            if col != 'date':
                keyword = col
                value = int(row[col]) if pd.notna(row[col]) else 0
                records.append((keyword, date, value, 'worldwide'))
    
    # Insert with conflict handling
    insert_query = """
        INSERT INTO trends_raw (keyword, date, value, region)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (keyword, date, region) 
        DO UPDATE SET value = EXCLUDED.value
    """
    
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Loaded {len(records)} records to trends_raw")
    
    cursor.close()
    conn.close()

def load_chatgpt_evolution():
    """Load ChatGPT evolution data"""
    print("\n📂 Loading ChatGPT evolution...")
    
    csv_path = 'data/processed/analytics/chatgpt_evolution_series.csv'
    
    if not os.path.exists(csv_path):
        print(f"   ⚠️  File not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    records = [(row['date'].date(), int(row['value']), float(row['rolling_28d_mean'])) 
               for _, row in df.iterrows()]
    
    insert_query = """
        INSERT INTO chatgpt_evolution (date, value, rolling_28d_mean)
        VALUES (%s, %s, %s)
        ON CONFLICT (date) 
        DO UPDATE SET value = EXCLUDED.value, rolling_28d_mean = EXCLUDED.rolling_28d_mean
    """
    
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Loaded {len(records)} records to chatgpt_evolution")
    
    cursor.close()
    conn.close()

def load_ai_peaks():
    """Load AI peaks data"""
    print("\n📂 Loading AI peaks...")
    
    csv_path = 'data/processed/analytics/ai_peaks.csv'
    
    if not os.path.exists(csv_path):
        print(f"   ⚠️  File not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print(f"   ℹ️  No peaks in file (stable data)")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    records = [(row['date'].date(), int(row['peak_value']), float(row['z_score']), 'AI') 
               for _, row in df.iterrows()]
    
    insert_query = """
        INSERT INTO ai_peaks (date, peak_value, z_score, keyword)
        VALUES (%s, %s, %s, %s)
    """
    
    cursor.execute("DELETE FROM ai_peaks WHERE keyword = 'AI'")
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Loaded {len(records)} records to ai_peaks")
    
    cursor.close()
    conn.close()

def load_geo_distribution():
    """Load geographic distribution"""
    print("\n📂 Loading geographic distribution...")
    
    csv_path = 'data/processed/analytics/python_top_countries.csv'
    
    if not os.path.exists(csv_path):
        print(f"   ⚠️  File not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    records = [('Python', row['region'], int(row['value']), idx + 1) 
               for idx, (_, row) in enumerate(df.iterrows())]
    
    insert_query = """
        INSERT INTO geo_distribution (keyword, region, value, rank)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (keyword, region) 
        DO UPDATE SET value = EXCLUDED.value, rank = EXCLUDED.rank
    """
    
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Loaded {len(records)} records to geo_distribution")
    
    cursor.close()
    conn.close()

def load_ml_comparison():
    """Load ML France vs USA comparison"""
    print("\n📂 Loading ML France vs USA comparison...")
    
    csv_path = 'data/processed/analytics/machine_learning_fr_us.csv'
    
    if not os.path.exists(csv_path):
        print(f"   ⚠️  File not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    records = [(row['date'].date(), int(row['fr_value']), int(row['us_value']), int(row['diff'])) 
               for _, row in df.iterrows()]
    
    insert_query = """
        INSERT INTO ml_comparison (date, fr_value, us_value, diff)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (date) 
        DO UPDATE SET fr_value = EXCLUDED.fr_value, us_value = EXCLUDED.us_value, diff = EXCLUDED.diff
    """
    
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Loaded {len(records)} records to ml_comparison")
    
    cursor.close()
    conn.close()

def load_ai_forecast():
    """Load AI forecast data"""
    print("\n📂 Loading AI forecast...")
    
    csv_path = 'data/processed/analytics/ai_forecast.csv'
    
    if not os.path.exists(csv_path):
        print(f"   ⚠️  File not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    records = [(row['date'].date(), float(row['forecast']), float(row['lower80']), float(row['upper80'])) 
               for _, row in df.iterrows()]
    
    insert_query = """
        INSERT INTO ai_forecast (date, forecast, lower_bound, upper_bound)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (date) 
        DO UPDATE SET forecast = EXCLUDED.forecast, lower_bound = EXCLUDED.lower_bound, upper_bound = EXCLUDED.upper_bound
    """
    
    cursor.execute("DELETE FROM ai_forecast")
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Loaded {len(records)} records to ai_forecast")
    
    cursor.close()
    conn.close()

def main():
    print("=" * 60)
    print("📥 Load CSV Data to PostgreSQL")
    print("=" * 60)
    
    try:
        # Test connection
        conn = get_db_connection()
        print("✅ Database connection successful\n")
        conn.close()
        
        # Load all data files
        load_raw_trends()
        load_chatgpt_evolution()
        load_ai_peaks()
        load_geo_distribution()
        load_ml_comparison()
        load_ai_forecast()
        
        print("\n" + "=" * 60)
        print("✅ All data loaded successfully!")
        print("=" * 60)
        
        # Show summary
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n📊 Database Summary:")
        tables = ['trends_raw', 'chatgpt_evolution', 'ai_peaks', 'geo_distribution', 'ml_comparison', 'ai_forecast']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table:25} {count:6} records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == '__main__':
    main()

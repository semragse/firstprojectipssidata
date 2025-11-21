#!/usr/bin/env python3
"""
Transform trends data and create analytics in PostgreSQL
"""
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch
from scipy import stats

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

def transform_chatgpt_evolution():
    """Transform ChatGPT data with rolling mean"""
    print("📊 Transforming ChatGPT evolution data...")
    
    conn = get_db_connection()
    
    # Read ChatGPT data
    query = """
        SELECT date, value 
        FROM trends_raw 
        WHERE keyword = 'ChatGPT' AND region = 'worldwide'
        ORDER BY date
    """
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("   ⚠️  No ChatGPT data found")
        conn.close()
        return
    
    # Calculate rolling mean (28 days / 4 weeks)
    df['rolling_28d_mean'] = df['value'].rolling(window=4, min_periods=1).mean()
    
    # Insert into chatgpt_evolution table
    cursor = conn.cursor()
    
    records = [(row['date'], int(row['value']), float(row['rolling_28d_mean'])) 
               for _, row in df.iterrows()]
    
    insert_query = """
        INSERT INTO chatgpt_evolution (date, value, rolling_28d_mean)
        VALUES (%s, %s, %s)
        ON CONFLICT (date) 
        DO UPDATE SET value = EXCLUDED.value, 
                     rolling_28d_mean = EXCLUDED.rolling_28d_mean
    """
    
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Transformed {len(records)} ChatGPT records")
    
    cursor.close()
    conn.close()

def detect_peaks(keyword, z_threshold=1.5):
    """Detect peaks in trends data using Z-score"""
    print(f"\n🔍 Detecting peaks for: {keyword} (threshold: {z_threshold})")
    
    conn = get_db_connection()
    
    # Read data
    query = f"""
        SELECT date, value 
        FROM trends_raw 
        WHERE keyword = '{keyword}' AND region = 'worldwide'
        ORDER BY date
    """
    df = pd.read_sql(query, conn)
    
    if df.empty or len(df) < 5:
        print(f"   ⚠️  Insufficient data for {keyword}")
        conn.close()
        return
    
    # Calculate rolling statistics (4 weeks window)
    df['rolling_mean'] = df['value'].rolling(window=4, min_periods=1).mean()
    df['rolling_std'] = df['value'].rolling(window=4, min_periods=1).std()
    
    # Calculate Z-score
    df['z_score'] = (df['value'] - df['rolling_mean']) / (df['rolling_std'] + 1e-10)
    
    # Detect peaks
    peaks = df[df['z_score'] > z_threshold]
    
    if peaks.empty:
        print(f"   ℹ️  No peaks detected (data is stable)")
        conn.close()
        return
    
    # Insert peaks
    cursor = conn.cursor()
    
    # Clear existing peaks for this keyword
    cursor.execute("DELETE FROM ai_peaks WHERE keyword = %s", (keyword,))
    
    records = [(row['date'], int(row['value']), float(row['z_score']), keyword) 
               for _, row in peaks.iterrows()]
    
    insert_query = """
        INSERT INTO ai_peaks (date, peak_value, z_score, keyword)
        VALUES (%s, %s, %s, %s)
    """
    
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Detected {len(records)} peaks")
    
    cursor.close()
    conn.close()

def generate_forecast(keyword='AI', horizon=30):
    """Generate simple forecast using naive seasonal method"""
    print(f"\n📈 Generating {horizon}-day forecast for: {keyword}")
    
    conn = get_db_connection()
    
    # Read recent data
    query = f"""
        SELECT date, value 
        FROM trends_raw 
        WHERE keyword = '{keyword}' AND region = 'worldwide'
        ORDER BY date DESC
        LIMIT 12
    """
    df = pd.read_sql(query, conn)
    
    if df.empty or len(df) < 7:
        print(f"   ⚠️  Insufficient data for forecasting")
        conn.close()
        return
    
    df = df.sort_values('date')
    
    # Simple forecast: use last 7 values and repeat with slight trend
    last_values = df['value'].tail(7).values
    last_date = df['date'].max()
    
    # Calculate trend
    trend = (df['value'].iloc[-1] - df['value'].iloc[0]) / len(df)
    
    # Generate forecast
    forecasts = []
    for i in range(1, horizon + 1):
        forecast_date = last_date + pd.Timedelta(days=i)
        # Repeat seasonal pattern with trend
        base_value = last_values[i % 7]
        forecast_value = base_value + (trend * i)
        
        # Calculate confidence interval (simple ±10%)
        lower = forecast_value * 0.9
        upper = forecast_value * 1.1
        
        forecasts.append((
            forecast_date.date(),
            float(forecast_value),
            float(lower),
            float(upper)
        ))
    
    # Insert forecasts
    cursor = conn.cursor()
    
    # Clear existing forecasts
    cursor.execute("DELETE FROM ai_forecast")
    
    insert_query = """
        INSERT INTO ai_forecast (date, forecast, lower_bound, upper_bound)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (date) 
        DO UPDATE SET forecast = EXCLUDED.forecast,
                     lower_bound = EXCLUDED.lower_bound,
                     upper_bound = EXCLUDED.upper_bound
    """
    
    execute_batch(cursor, insert_query, forecasts)
    conn.commit()
    
    print(f"   ✅ Generated {len(forecasts)} forecast points")
    
    cursor.close()
    conn.close()

def main():
    print("=" * 60)
    print("🔄 Transform Trends Data in PostgreSQL")
    print("=" * 60)
    
    # Transform ChatGPT evolution
    transform_chatgpt_evolution()
    
    # Detect peaks for AI and Data Science
    detect_peaks('AI', z_threshold=1.5)
    detect_peaks('Data Science', z_threshold=1.5)
    
    # Generate forecast
    generate_forecast('AI', horizon=30)
    
    print("\n" + "=" * 60)
    print("✅ Transformation complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

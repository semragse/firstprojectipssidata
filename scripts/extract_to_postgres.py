#!/usr/bin/env python3
"""
Extract Google Trends data and load directly to PostgreSQL
"""
import sys
import argparse
import warnings
from datetime import datetime, timedelta
import pandas as pd
from pytrends.request import TrendReq
import psycopg2
from psycopg2.extras import execute_batch

warnings.filterwarnings('ignore')

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

def extract_trends(keywords, timeframe='today 12-m', insecure=False):
    """Extract Google Trends data"""
    print(f"🔍 Extracting trends for: {', '.join(keywords)}")
    print(f"   Timeframe: {timeframe}")
    
    # Configure PyTrends with SSL settings
    requests_args = {}
    if insecure:
        requests_args['verify'] = False
        print("   ⚠️  SSL verification disabled (corporate proxy mode)")
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, requests_args=requests_args)
        
        # Build payload
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo='', gprop='')
        
        # Get interest over time
        df = pytrends.interest_over_time()
        
        if df.empty:
            print("   ❌ No data retrieved")
            return None
        
        # Remove 'isPartial' column if exists
        if 'isPartial' in df.columns:
            df = df.drop(columns=['isPartial'])
        
        print(f"   ✅ Retrieved {len(df)} data points")
        return df
    
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def load_to_postgres(df, keywords):
    """Load trends data to PostgreSQL"""
    print(f"\n💾 Loading data to PostgreSQL...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Prepare data for insertion
    records = []
    for date, row in df.iterrows():
        for keyword in keywords:
            if keyword in row:
                records.append((
                    keyword,
                    date.date(),
                    int(row[keyword]),
                    'worldwide'
                ))
    
    # Insert data (ON CONFLICT DO UPDATE to handle duplicates)
    insert_query = """
        INSERT INTO trends_raw (keyword, date, value, region)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (keyword, date, region) 
        DO UPDATE SET value = EXCLUDED.value
    """
    
    execute_batch(cursor, insert_query, records)
    conn.commit()
    
    print(f"   ✅ Loaded {len(records)} records to database")
    
    cursor.close()
    conn.close()

def extract_geographic_data(keyword, insecure=False):
    """Extract geographic distribution for a keyword"""
    print(f"\n🌍 Extracting geographic data for: {keyword}")
    
    requests_args = {}
    if insecure:
        requests_args['verify'] = False
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, requests_args=requests_args)
        pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo='', gprop='')
        
        # Get interest by region
        df = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True, inc_geo_code=False)
        df = df.sort_values(by=keyword, ascending=False).head(10)
        
        if df.empty:
            print("   ⚠️  No geographic data available")
            return
        
        # Load to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        records = []
        for rank, (region, row) in enumerate(df.iterrows(), 1):
            records.append((
                keyword,
                region,
                int(row[keyword]),
                rank
            ))
        
        insert_query = """
            INSERT INTO geo_distribution (keyword, region, value, rank)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (keyword, region) 
            DO UPDATE SET value = EXCLUDED.value, rank = EXCLUDED.rank
        """
        
        execute_batch(cursor, insert_query, records)
        conn.commit()
        
        print(f"   ✅ Loaded {len(records)} geographic records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def extract_comparison_data(keyword, regions, insecure=False):
    """Extract comparison data between regions"""
    print(f"\n🆚 Extracting comparison: {keyword} ({' vs '.join(regions)})")
    
    requests_args = {}
    if insecure:
        requests_args['verify'] = False
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, requests_args=requests_args)
        
        # Get data for each region
        dfs = []
        for region in regions:
            pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo=region, gprop='')
            df_region = pytrends.interest_over_time()
            if not df_region.empty and keyword in df_region.columns:
                df_region = df_region[[keyword]].rename(columns={keyword: region})
                dfs.append(df_region)
        
        if len(dfs) != 2:
            print("   ⚠️  Could not retrieve data for both regions")
            return
        
        # Merge data
        df_merged = dfs[0].join(dfs[1], how='inner')
        df_merged['diff'] = df_merged[regions[0]] - df_merged[regions[1]]
        
        # Load to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        records = []
        for date, row in df_merged.iterrows():
            records.append((
                date.date(),
                int(row[regions[0]]),
                int(row[regions[1]]),
                int(row['diff'])
            ))
        
        insert_query = """
            INSERT INTO ml_comparison (date, fr_value, us_value, diff)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (date) 
            DO UPDATE SET fr_value = EXCLUDED.fr_value, 
                         us_value = EXCLUDED.us_value,
                         diff = EXCLUDED.diff
        """
        
        execute_batch(cursor, insert_query, records)
        conn.commit()
        
        print(f"   ✅ Loaded {len(records)} comparison records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Extract Google Trends data to PostgreSQL')
    parser.add_argument('--keywords', nargs='+', 
                       default=['ChatGPT', 'AI', 'Machine Learning', 'Python', 'Data Science'],
                       help='Keywords to track')
    parser.add_argument('--timeframe', default='today 12-m',
                       help='Timeframe for data extraction')
    parser.add_argument('--insecure', action='store_true',
                       help='Disable SSL verification (for corporate proxies)')
    parser.add_argument('--geo', action='store_true',
                       help='Also extract geographic data')
    parser.add_argument('--comparison', action='store_true',
                       help='Extract FR vs US comparison for Machine Learning')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Google Trends to PostgreSQL Extractor")
    print("=" * 60)
    
    # Extract main trends
    df = extract_trends(args.keywords, args.timeframe, args.insecure)
    if df is not None:
        load_to_postgres(df, args.keywords)
    
    # Extract geographic data if requested
    if args.geo:
        extract_geographic_data('Python', args.insecure)
    
    # Extract comparison data if requested
    if args.comparison:
        extract_comparison_data('Machine Learning', ['FR', 'US'], args.insecure)
    
    print("\n" + "=" * 60)
    print("✅ Extraction complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

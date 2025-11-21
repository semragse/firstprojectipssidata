-- Load CSV data using COPY commands

-- First, let's create a temp table to load the raw CSV
CREATE TEMP TABLE temp_raw (
    date TEXT,
    chatgpt TEXT,
    ai TEXT,
    machine_learning TEXT,
    python TEXT,
    data_science TEXT
);

\COPY temp_raw FROM '/tmp/data/raw/google_trends_daily_20241120_20251120.csv' WITH (FORMAT CSV, HEADER);

-- Insert into trends_raw
INSERT INTO trends_raw (keyword, date, value, region)
SELECT 'ChatGPT', date::date, COALESCE(chatgpt::integer, 0), 'worldwide' FROM temp_raw
UNION ALL
SELECT 'AI', date::date, COALESCE(ai::integer, 0), 'worldwide' FROM temp_raw
UNION ALL
SELECT 'Machine Learning', date::date, COALESCE(machine_learning::integer, 0), 'worldwide' FROM temp_raw
UNION ALL
SELECT 'Python', date::date, COALESCE(python::integer, 0), 'worldwide' FROM temp_raw
UNION ALL
SELECT 'Data Science', date::date, COALESCE(data_science::integer, 0), 'worldwide' FROM temp_raw
ON CONFLICT (keyword, date, region) DO UPDATE SET value = EXCLUDED.value;

-- Load ChatGPT evolution
\COPY chatgpt_evolution (date, value, rolling_28d_mean) FROM '/tmp/data/processed/analytics/chatgpt_evolution_series.csv' WITH (FORMAT CSV, HEADER) ON CONFLICT (date) DO UPDATE SET value = EXCLUDED.value, rolling_28d_mean = EXCLUDED.rolling_28d_mean;

-- Load python top countries
\COPY geo_distribution (region, value) FROM '/tmp/data/processed/analytics/python_top_countries.csv' WITH (FORMAT CSV, HEADER);

UPDATE geo_distribution SET keyword = 'Python';

-- Load ML comparison
\COPY ml_comparison (date, fr_value, us_value, diff) FROM '/tmp/data/processed/analytics/machine_learning_fr_us.csv' WITH (FORMAT CSV, HEADER) ON CONFLICT (date) DO UPDATE SET fr_value = EXCLUDED.fr_value, us_value = EXCLUDED.us_value, diff = EXCLUDED.diff;

-- Load AI forecast
\COPY ai_forecast (date, forecast, lower_bound, upper_bound) FROM '/tmp/data/processed/analytics/ai_forecast.csv' WITH (FORMAT CSV, HEADER) ON CONFLICT (date) DO UPDATE SET forecast = EXCLUDED.forecast, lower_bound = EXCLUDED.lower_bound, upper_bound = EXCLUDED.upper_bound;

-- Show summary
SELECT 'trends_raw' as table_name, COUNT(*) as records FROM trends_raw
UNION ALL
SELECT 'chatgpt_evolution', COUNT(*) FROM chatgpt_evolution
UNION ALL
SELECT 'geo_distribution', COUNT(*) FROM geo_distribution
UNION ALL
SELECT 'ml_comparison', COUNT(*) FROM ml_comparison
UNION ALL
SELECT 'ai_forecast', COUNT(*) FROM ai_forecast;

-- Initialize database schema for Google Trends data

-- Table for raw trends data
CREATE TABLE IF NOT EXISTS trends_raw (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    value INTEGER NOT NULL,
    region VARCHAR(10) DEFAULT 'worldwide',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, date, region)
);

-- Table for ChatGPT evolution
CREATE TABLE IF NOT EXISTS chatgpt_evolution (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    value INTEGER NOT NULL,
    rolling_28d_mean DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for detected peaks
CREATE TABLE IF NOT EXISTS ai_peaks (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    peak_value INTEGER NOT NULL,
    z_score DECIMAL(10,3) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for geographic distribution
CREATE TABLE IF NOT EXISTS geo_distribution (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    value INTEGER NOT NULL,
    rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, region)
);

-- Table for ML France vs USA comparison
CREATE TABLE IF NOT EXISTS ml_comparison (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    fr_value INTEGER NOT NULL,
    us_value INTEGER NOT NULL,
    diff INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for forecasts
CREATE TABLE IF NOT EXISTS ai_forecast (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    forecast DECIMAL(10,2) NOT NULL,
    lower_bound DECIMAL(10,2),
    upper_bound DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_trends_raw_keyword_date ON trends_raw(keyword, date);
CREATE INDEX idx_trends_raw_date ON trends_raw(date);
CREATE INDEX idx_chatgpt_evolution_date ON chatgpt_evolution(date);
CREATE INDEX idx_ai_peaks_date ON ai_peaks(date);
CREATE INDEX idx_ml_comparison_date ON ml_comparison(date);
CREATE INDEX idx_ai_forecast_date ON ai_forecast(date);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trends_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trends_user;

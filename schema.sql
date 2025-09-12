-- This script creates the two tables we need for our project.

-- Create the daily_stock_data table to store raw API data.
-- This table is designed to capture key metrics for each day.
CREATE TABLE IF NOT EXISTS daily_stock_data (
    date DATE PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    open DECIMAL(10, 4),
    high DECIMAL(10, 4),
    low DECIMAL(10, 4),
    close DECIMAL(10, 4),
    adjusted_close DECIMAL(10, 4),
    volume BIGINT,
    dividend_amount DECIMAL(10, 4),
    split_coefficient DECIMAL(10, 4),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create the daily_recommendations table to store the LLM's output.
-- This is where the AI's summary and recommendations will be saved.
CREATE TABLE IF NOT EXISTS daily_recommendations (
    id SERIAL PRIMARY KEY,
    analysis_date DATE NOT NULL,
    llm_summary TEXT NOT NULL,
    recommendation_1 TEXT,
    recommendation_2 TEXT,
    recommendation_3 TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Add an index for faster lookups on the analysis date.
CREATE INDEX idx_analysis_date ON daily_recommendations (analysis_date);

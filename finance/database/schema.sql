-- Finance Market PostgreSQL Database Schema
-- Database: finance_market

-- Enable TimescaleDB Extension if available
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Virtual Wallets Table
CREATE TABLE IF NOT EXISTS wallets (
    user_id INT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    balance NUMERIC(15, 2) NOT NULL DEFAULT 1000000.00, -- 10 Lakh INR Initial Balance
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Paper Trades (Orders) Table
CREATE TABLE IF NOT EXISTS paper_trades (
    id VARCHAR(64) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    instrument_type VARCHAR(20) NOT NULL DEFAULT 'EQ', -- CE / PE / EQ
    strike_price NUMERIC(12, 2) DEFAULT 0.00,
    expiry VARCHAR(30) DEFAULT '',
    transaction_type VARCHAR(10) NOT NULL, -- BUY / SELL
    quantity INT NOT NULL,
    entry_price NUMERIC(12, 2) NOT NULL,
    entry_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    exit_price NUMERIC(12, 2),
    exit_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN', -- OPEN / CLOSED / CANCELLED
    stop_loss NUMERIC(12, 2) DEFAULT 0.00,
    target NUMERIC(12, 2) DEFAULT 0.00,
    pnl NUMERIC(15, 2) DEFAULT 0.00
);

-- 4. Transaction Ledger Table (Audit Trail)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trade_id VARCHAR(64) REFERENCES paper_trades(id) ON DELETE SET NULL,
    type VARCHAR(20) NOT NULL, -- DEBIT / CREDIT / MARGIN_HOLD
    amount NUMERIC(15, 2) NOT NULL,
    balance_after NUMERIC(15, 2) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Candles / Historical OHLCV Table (TimescaleDB Optimized)
CREATE TABLE IF NOT EXISTS candles (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (symbol, time)
);

-- Create hypertable for candles if TimescaleDB extension is active
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('candles', 'time', if_not_exists => TRUE);
    END IF;
END $$;
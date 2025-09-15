-- backend/schema.sql

CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    short_window INT,
    long_window INT,
    stop_loss_pct FLOAT,
    take_profit_pct FLOAT,
    initial_capital FLOAT,
    total_return_pct FLOAT,
    max_drawdown_pct FLOAT,
    sharpe FLOAT,
    n_trades INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    backtest_id INT,
    timestamp TIMESTAMP,
    side VARCHAR(10),
    price FLOAT,
    size INT,
    pnl FLOAT,
    cumulative_return_pct FLOAT
);

CREATE TABLE IF NOT EXISTS ohlc (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    timestamp TIMESTAMP,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT
);

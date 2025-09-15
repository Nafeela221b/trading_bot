# backend/backtest.py
import os
import math
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, MetaData, Table, insert, select
from sqlalchemy.dialects.postgresql import TIMESTAMP
from dotenv import load_dotenv
import datetime as dt

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://trader:password@localhost:5432/trading_db")
engine = create_engine(DB_URL, future=True)
meta = MetaData()

# Define tables (mirror schema.sql)
backtests = Table(
    "backtests", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("symbol", String, nullable=False),
    Column("start_date", DateTime),
    Column("end_date", DateTime),
    Column("short_window", Integer),
    Column("long_window", Integer),
    Column("stop_loss_pct", Float),
    Column("take_profit_pct", Float),
    Column("initial_capital", Float),
    Column("total_return_pct", Float),
    Column("max_drawdown_pct", Float),
    Column("sharpe", Float),
    Column("n_trades", Integer),
    Column("created_at", TIMESTAMP, default=dt.datetime.utcnow)
)

trades = Table(
    "trades", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("backtest_id", Integer),
    Column("timestamp", TIMESTAMP),
    Column("side", String),  # BUY/SELL
    Column("price", Float),
    Column("size", Integer),
    Column("pnl", Float),
    Column("cumulative_return_pct", Float)
)

ohlc = Table(
    "ohlc", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("symbol", String),
    Column("timestamp", TIMESTAMP),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("volume", Float)
)

meta.create_all(engine)

# ---- helper functions ----
def fetch_ohlc(symbol, period="2y", interval="1d"):
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)

    if df is None or df.empty:
        raise ValueError(f"No OHLC data returned for symbol: {symbol}")

    if isinstance(df.columns, pd.MultiIndex):
        # Drop second level (ticker) if it's multi-level like ('Open', 'AAPL')
        df.columns = df.columns.droplevel(1)

    df = df.rename_axis('timestamp').reset_index()

    expected_cols = ['Open','High','Low','Close','Volume']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in OHLC data: {missing_cols}")

    df = df[['timestamp','Open','High','Low','Close','Volume']].rename(columns={
        'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'
    })

    return df


def generate_signals(df, short_window=20, long_window=50):
    df = df.copy()
    df['sma_short'] = df['close'].rolling(short_window).mean()
    df['sma_long'] = df['close'].rolling(long_window).mean()
    df['signal'] = 0
    df.loc[(df['sma_short'] > df['sma_long']) & (df['sma_short'].shift(1) <= df['sma_long'].shift(1)), 'signal'] = 1
    df.loc[(df['sma_short'] < df['sma_long']) & (df['sma_short'].shift(1) >= df['sma_long'].shift(1)), 'signal'] = -1
    return df

def run_backtest(df, initial_capital=10000, stop_loss_pct=0.01, take_profit_pct=0.5):
    cash = initial_capital
    position = 0
    entry_price = 0.0
    trades_list = []
    portfolio_values = []

    for idx, row in df.iterrows():
        price = row['close']
        date = row['timestamp']
        #signal = row['signal']
        signal = row.get('signal', 0)
        #print(f"row index: {idx}, type: {type(row['signal'])}, value: {row['signal']}")
        if pd.isna(signal):
            signal = 0
        signal = int(signal)

        # check stop loss / take profit if in position
        if position > 0:
            current_return = (price - entry_price) / entry_price
            if current_return <= -stop_loss_pct:
                cash += position * price
                trades_list.append({'timestamp': date, 'side':'SELL','price':price,'size':position,'pnl': (price-entry_price)*position})
                position = 0
                entry_price = 0
                portfolio_values.append(cash + position*price)
                continue
            if current_return >= take_profit_pct:
                cash += position * price
                trades_list.append({'timestamp': date, 'side':'SELL','price':price,'size':position,'pnl': (price-entry_price)*position})
                position = 0
                entry_price = 0
                portfolio_values.append(cash + position*price)
                continue

        # process signals
        if signal == 1 and position == 0:
            size = math.floor(cash / price)
            if size > 0:
                entry_price = price
                position = size
                cash -= size * price
                trades_list.append({'timestamp': date, 'side':'BUY','price':price,'size':size,'pnl':0.0})
        elif signal == -1 and position > 0:
            cash += position * price
            trades_list.append({'timestamp': date, 'side':'SELL','price':price,'size':position,'pnl': (price-entry_price)*position})
            position = 0
            entry_price = 0

        portfolio_values.append(cash + position*price)

    final_value = cash + position * (df.iloc[-1]['close'] if position>0 else 0)
    returns = pd.Series(portfolio_values).pct_change().fillna(0.0)
    sharpe = (returns.mean() / returns.std(ddof=1)) * (252**0.5) if returns.std() != 0 else 0.0

    cumulative = pd.Series(portfolio_values).cummax()
    drawdown = (pd.Series(portfolio_values) - cumulative) / cumulative
    max_drawdown = drawdown.min()

    results = {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return_pct': (final_value - initial_capital) / initial_capital * 100,
        'max_drawdown_pct': float(max_drawdown * 100),
        'sharpe': float(sharpe),
        'n_trades': len(trades_list)
    }
    return results, trades_list, portfolio_values

def save_backtest_results(name, symbol, df, results, trades_list, short_window, long_window, stop_loss_pct, take_profit_pct):
    with engine.begin() as conn:
        res = conn.execute(
            insert(backtests).values(
                name=name, symbol=symbol,
                start_date=df['timestamp'].min(), end_date=df['timestamp'].max(),
                short_window=short_window, long_window=long_window,
                stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct,
                initial_capital=10000,
                total_return_pct=results['total_return_pct'],
                max_drawdown_pct=results['max_drawdown_pct'],
                sharpe=results['sharpe'],
                n_trades=results['n_trades'],
            )
        )
        backtest_id = res.inserted_primary_key[0]

        # ohlc rows insert (batch)
        ohlc_rows = [
            {'symbol': symbol, 'timestamp': r['timestamp'], 'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close'], 'volume': float(r['volume'])}
            for i, r in df.iterrows()
        ]
        if ohlc_rows:
            conn.execute(ohlc.insert(), ohlc_rows)

        # trades
        cumulative = 0.0
        trade_rows = []
        for t in trades_list:
            pnl = t['pnl']
            cumulative += pnl
            trade_rows.append({'backtest_id': backtest_id, 'timestamp': t['timestamp'], 'side': t['side'], 'price': t['price'], 'size': t['size'], 'pnl': pnl, 'cumulative_return_pct': cumulative})
        if trade_rows:
            conn.execute(trades.insert(), trade_rows)

    return backtest_id

def run_example(symbol="MSFT", period="2y", interval="1d", short_window=10, long_window=40):
    print(f"Fetching {symbol} data...")
    df = fetch_ohlc(symbol, period=period, interval=interval)
    print("Fetched OHLC data:\n", df.head())

    df = generate_signals(df, short_window, long_window)
    results, trades_list, portvals = run_backtest(df, initial_capital=10000, stop_loss_pct=0.01, take_profit_pct=0.5)
    bt_id = save_backtest_results(f"MAC_{symbol}_{short_window}_{long_window}", symbol, df, results, trades_list, short_window, long_window, 0.01, 0.5)
    print("Backtest saved to DB with id:", bt_id)
    print("Results:", results)

if __name__ == "__main__":
    run_example("AAPL")

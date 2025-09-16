# run_strategy.py
from lumibot.backtesting import YahooDataBacktesting
from lumibot_strategy import SMACrossoverStrategy
from datetime import datetime
import psycopg2
import os

# Backtest parameters
start_date = datetime(2022, 1, 1)
end_date = datetime(2023, 1, 10)
initial_cash = 100000

# Create folder if it doesn’t exist
os.makedirs("results", exist_ok=True)

# Run backtest
results = SMACrossoverStrategy.backtest(
    strategy_name="SMACrossover",
    cash=initial_cash,
    datasource_class=YahooDataBacktesting,
    start=start_date,
    end=end_date,
    stats_file="results/trade_results.csv",
    plot_file="results/trade_results.png",
    benchmark_asset="SPY"
)

print("Backtest completed!")

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="trading_db",
    user="trader",
    password="root"
)
cursor = conn.cursor()



# Insert trades into trades table
for trade in SMACrossoverStrategy.trades_list:

    # Convert Unix timestamp to datetime
    ts = datetime.fromtimestamp(trade["datetime"])

    cursor.execute("""
        INSERT INTO trades (backtest_id, timestamp, side, price, size, pnl, cumulative_return_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        1,  # backtest_id
        ts,
        trade["action"],
        float(trade["price"]),
        int(trade["size"]),
        float(trade["pnl"]),
        float(trade["cumulative_return_pct"])
    ))

conn.commit()
cursor.close()
conn.close()
print(f"{len(SMACrossoverStrategy.trades_list)} trades inserted into PostgreSQL")

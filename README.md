1. Project Overview:
This project demonstrates a Moving Average Crossover (MAC) trading strategy implemented using Python, Lumibot, and PostgreSQL, with visualization in React using Lightweight Charts.
The goal is to:
1. Backtest a trading strategy using historical OHLC data.
2. Implement stop-loss and take-profit mechanisms.
3. Store results in a structured PostgreSQL database for easy comparison.
4. Display results and trades on an interactive frontend chart.

2. Strategy Details:
The Simple Moving Average (SMA) Crossover strategy involves:
- Short-term SMA: 20-day moving average
- Long-term SMA: 50-day moving average

Trading signals:
- Short SMA crosses above Long SMA	--> BUY 
- Short SMA crosses below Long SMA	--> SELL 
- Position loss ≥ 1%	-> STOP-LOSS SELL
- Position profit ≥ 50%	--> TAKE-PROFIT SELL

3. Python Implementation:
- Libraries Used: Pandas, NumPy, yfinance, SQLAlchemy, Lumibot.
- Backtesting Logic:
  - Fetch historical OHLC data using YahooDataBacktesting.
  - Generate signals based on SMA crossover.
  - Execute trades with stop-loss and take-profit.
  - Track portfolio value, cumulative returns, and performance metrics.

4. Project Structure
project/
│
├─ backend/
│   ├─ backtest.py
│   ├─ db.py
│   ├─ api.py
│   ├─ lumibot_strategy.py
│   ├─ run_strategy.py
│   └─ schema.sql
│
├─ frontend/
│   ├─ App.tsx
│   └─ components/
│       └─ Chart.tsx
│
├─ docker-compose.yml
├─ .env
└─ README.docx


9. How to Run
- Start PostgreSQL using Docker:
docker-compose up -d

- Install Python dependencies:
pip install -r requirements.txt

- Run Backtests:
python backend/run_strategy.py

- Start FastAPI Backend:
uvicorn backend/api:app --reload

- Start Frontend:
npm install
npm start

10. References:
- Lumibot Documentation: https://lumibot.lumiwealth.com/
- Lightweight Charts: https://github.com/tradingview/lightweight-charts
- SQLAlchemy ORM: https://www.sqlalchemy.org/
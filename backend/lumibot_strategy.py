# backend/lumibot_strategy.py
# A small skeleton demonstrating how you'd implement the SMA crossover in Lumibot style.
from lumibot.strategies.strategy import Strategy
import pandas as pd

class MACrossoverLumibot(Strategy):
    def __init__(self, symbol="AAPL", short=20, long=50):
        super().__init__()
        self.symbol = symbol
        self.short = short
        self.long = long

    def on_trading_iteration(self):
        df = self.get_historical_prices(self.symbol, length=self.long)
        closes = df['close']
        if len(closes) < self.long:
            return
        sma_short = closes[-self.short:].mean()
        sma_long = closes[-self.long:].mean()
        # Add buy/sell based on cross — exact lumibot method names may vary

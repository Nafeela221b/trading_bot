
# lumibot_strategy.py
import pandas as pd
from lumibot.strategies.strategy import Strategy

class SMACrossoverStrategy(Strategy):
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]  # Add more symbols as needed
    short_window = 5
    long_window = 50
    stop_loss_pct = 0.01
    take_profit_pct = 0.5
    trades_list = []  # store trades manually
    portfolio_value = 100000  # starting cash
    cumulative_return = 0

    def on_trading_iteration(self):
        for ticker in self.tickers:
            bars = self.get_historical_prices(ticker, length=self.long_window)
            if len(bars) < self.long_window:
                continue

            # Convert Bars -> DataFrame
            df = bars.df.copy()
            closes = df["close"]

            sma_short = closes[-self.short_window:].mean()
            sma_long = closes[-self.long_window:].mean()

            position = self.get_position(ticker)
            current_price = closes.iloc[-1]

            # BUY signal
            if sma_short > sma_long and position is None:
                qty = int(self.cash // current_price)
                if qty > 0:
                    self.create_order(ticker, qty, "buy")
                    self.trades_list.append({
                        "ticker": ticker,
                        "action": "BUY",
                        "price": current_price,
                        "size": qty,
                        "pnl": 0,
                        "cumulative_return_pct": self.cumulative_return,
                        "datetime": self.get_timestamp()
                    })

            # SELL signal or Stop Loss / Take Profit
            elif position is not None:
                buy_price = position.cost_basis

                # Stop loss
                if current_price <= buy_price * (1 - self.stop_loss_pct):
                    self.create_order(ticker, position.quantity, "sell")
                    pnl = (current_price - buy_price) * position.quantity
                    self.cumulative_return += pnl / self.portfolio_value * 100
                    self.trades_list.append({
                        "ticker": ticker,
                        "action": "SELL_STOPLOSS",
                        "price": current_price,
                        "size": position.quantity,
                        "pnl": pnl,
                        "cumulative_return_pct": self.cumulative_return,
                        "datetime": self.get_timestamp()
                    })

                # Take profit
                elif current_price >= buy_price * (1 + self.take_profit_pct):
                    self.create_order(ticker, position.quantity, "sell")
                    pnl = (current_price - buy_price) * position.quantity
                    self.cumulative_return += pnl / self.portfolio_value * 100
                    self.trades_list.append({
                        "ticker": ticker,
                        "action": "SELL_TAKEPROFIT",
                        "price": current_price,
                        "size": position.quantity,
                        "pnl": pnl,
                        "cumulative_return_pct": self.cumulative_return,
                        "datetime": self.get_timestamp()
                    })

                # SMA cross down
                elif sma_short < sma_long:
                    self.create_order(ticker, position.quantity, "sell")
                    pnl = (current_price - buy_price) * position.quantity
                    self.cumulative_return += pnl / self.portfolio_value * 100
                    self.trades_list.append({
                        "ticker": ticker,
                        "action": "SELL",
                        "price": current_price,
                        "size": position.quantity,
                        "pnl": pnl,
                        "cumulative_return_pct": self.cumulative_return,
                        "datetime": self.get_timestamp()
                    })

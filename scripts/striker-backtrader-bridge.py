#!/home/synczus/kestrel/.venv/bin/python
"""
Striker → Backtrader Bridge
Reads Striker signals from SQLite, feeds into Backtrader for backtesting + live.
"""
import sqlite3, backtrader as bt
import pandas as pd
from datetime import datetime, timedelta

SIGNALS_DB = "/home/synczus/kestrel/kestrel_signals.db"
OR_METER = "🟢 OR Meter [████████████░░░░░░░░] $32.39/$50.00 ($17.61 left)"

class StrikerMomentum(bt.Strategy):
    """Momentum strategy using Striker signal data."""
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=3)
        self.cross = bt.indicators.CrossOver(self.data.close, self.sma)
    
    def next(self):
        if self.cross > 0:  # Price crossed above SMA
            self.buy(size=10)
        elif self.cross < 0:  # Price crossed below SMA
            self.close()

def load_signal_bars(symbol="SOL-USD", window_minutes=120):
    """Load Striker signals and resample into OHLC bars."""
    conn = sqlite3.connect(SIGNALS_DB)
    df = pd.read_sql_query(
        f"SELECT timestamp, price FROM signals WHERE symbol=? ORDER BY timestamp",
        conn, parse_dates=['timestamp'], params=(symbol,)
    )
    conn.close()
    
    if df.empty:
        print(f"⚠️  No signals for {symbol}")
        return None
    
    df.set_index('timestamp', inplace=True)
    bars = df['price'].resample('1min').ohlc().dropna()
    bar_counts = df['price'].resample('1min').count()
    bar_counts = bar_counts[bars.index]
    bars['volume'] = bar_counts.values
    return bars

def backtest(symbol="SOL-USD", window_minutes=120):
    """Run backtest on Striker signal data."""
    bars = load_signal_bars(symbol, window_minutes)
    if bars is None or bars.empty:
        return
    
    print(f"📊 {symbol} — {len(bars)} minute-bars loaded from Striker")
    print(f"💵 Starting capital: $1,000.00")
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(StrikerMomentum)
    cerebro.adddata(bt.feeds.PandasData(dataname=bars))
    cerebro.broker.setcash(1000.0)
    
    start = cerebro.broker.getvalue()
    cerebro.run()
    end = cerebro.broker.getvalue()
    
    pnl = ((end / start) - 1) * 100
    status = "📈 PROFIT" if pnl > 0 else "📉 LOSS" if pnl < 0 else "⚪ FLAT"
    print(f"  {status}: ${start:.2f} → ${end:.2f} ({pnl:.2f}%)")
    return pnl

if __name__ == "__main__":
    print("=== Striker → Backtrader Backtest ===\n")
    for sym in ["SOL-USD", "ETH-USD", "BTC-USD"]:
        backtest(sym, 120)
    print(f"\n{OR_METER}")

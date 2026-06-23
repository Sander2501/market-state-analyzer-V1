import pandas as pd

from backtesting.engine import backtest_market_state
from core.indicators import add_indicators


def test_backtest_returns_trade_log_and_benchmark():
    closes = list(range(100, 180))
    data = add_indicators(pd.DataFrame({
        "Open": closes,
        "High": [value + 1 for value in closes],
        "Low": [value - 1 for value in closes],
        "Close": closes,
        "Volume": [1000] * len(closes),
    }))

    result = backtest_market_state(data, holding_days=5)

    assert "signals" in result
    assert "benchmark" in result
    assert "trade_log" in result

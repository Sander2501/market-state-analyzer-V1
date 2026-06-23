import pandas as pd

from core.indicators import add_indicators
from backtesting.engine import backtest_market_state


def test_backtest_returns_expected_keys():
    data = pd.DataFrame({
        "Open": range(1, 151),
        "High": range(2, 152),
        "Low": range(0, 150),
        "Close": range(1, 151),
    })

    data = add_indicators(data)

    result = backtest_market_state(data)

    assert "signals" in result
    assert "benchmark" in result
    assert "trade_log" in result

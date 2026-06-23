import pandas as pd

from backtesting.engine import backtest_market_state
from core.indicators import add_indicators


def _data(closes: list[float]) -> pd.DataFrame:
    return add_indicators(pd.DataFrame({
        "Open": closes,
        "High": [value + 1 for value in closes],
        "Low": [value - 1 for value in closes],
        "Close": closes,
        "Volume": [1000] * len(closes),
    }))


def test_backtest_returns_trade_log_and_benchmark():
    result = backtest_market_state(_data(list(range(100, 180))), holding_days=5)

    assert "signals" in result
    assert "benchmark" in result
    assert "trade_log" in result


def test_backtest_summaries_include_confidence():
    result = backtest_market_state(_data(list(range(100, 180))), holding_days=5)

    assert all("confidence" in stats for stats in result["signals"].values())


def test_backtest_can_exit_on_atr_take_profit():
    data = pd.DataFrame({
        "Open": [100, 100, 101, 102, 103, 104, 105],
        "High": [101, 101, 103, 104, 105, 106, 107],
        "Low": [99, 99, 100, 101, 102, 103, 104],
        "Close": [100, 100, 101, 102, 103, 104, 105],
        "SMA_20": [90] * 7,
        "SMA_50": [80] * 7,
        "RSI_14": [60] * 7,
        "ATR_14": [2] * 7,
    })

    result = backtest_market_state(
        data,
        holding_days=5,
        use_risk_exits=True,
        stop_atr_multiplier=3,
        take_profit_atr_multiplier=0.5,
    )

    assert result["trade_log"][0]["Exit Reason"] == "Take profit"

import pandas as pd

from backtesting.engine import backtest_market_state, build_equity_curves
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



def test_backtest_can_exit_short_on_take_profit():
    data = pd.DataFrame({
        "Open": [100, 100, 99, 98, 97, 96, 95],
        "High": [101, 101, 100, 99, 98, 97, 96],
        "Low": [99, 99, 97, 96, 95, 94, 93],
        "Close": [100, 100, 99, 98, 97, 96, 95],
        "SMA_20": [110] * 7,
        "SMA_50": [120] * 7,
        "RSI_14": [40] * 7,
        "ATR_14": [2] * 7,
    })

    result = backtest_market_state(
        data,
        holding_days=5,
        use_risk_exits=True,
        stop_atr_multiplier=3,
        take_profit_atr_multiplier=0.5,
    )

    assert result["trade_log"][0]["Direction"] == "short"
    assert result["trade_log"][0]["Exit Reason"] == "Take profit"


def test_backtest_can_exit_on_stop_loss():
    data = pd.DataFrame({
        "Open": [100, 100, 99, 98, 97, 96, 95],
        "High": [101, 105, 106, 107, 108, 109, 110],
        "Low": [99, 99, 98, 97, 96, 95, 94],
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
        stop_atr_multiplier=0.5,
        take_profit_atr_multiplier=5,
    )

    assert result["trade_log"][0]["Exit Reason"] == "Stop loss"


def test_build_equity_curves_compares_strategy_and_benchmark():
    data = _data(list(range(100, 180)))
    backtest = backtest_market_state(data, holding_days=5)
    curves = build_equity_curves(data, backtest["trade_log"])

    assert list(curves.columns) == ["Buy & Hold", "Strategy"]
    assert curves["Buy & Hold"].iloc[0] == 1
    assert curves["Strategy"].iloc[0] == 1

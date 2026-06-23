import pandas as pd

from core.signals import get_signal, get_trade_direction


def test_get_signal_bullish_trend():
    row = pd.Series({
        "Close": 120,
        "SMA_20": 110,
        "SMA_50": 100,
        "RSI_14": 60,
    })

    assert get_signal(row) == "Bullish trend"


def test_get_trade_direction():
    assert get_trade_direction("Bullish trend") == "long"
    assert get_trade_direction("Bearish trend") == "short"
    assert get_trade_direction("Neutral") == "none"

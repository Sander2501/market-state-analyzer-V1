from core.signals import get_signal, get_trade_direction


def test_bullish_trend_signal():
    row = {
        "Close": 120,
        "SMA_20": 100,
        "SMA_50": 90,
        "RSI_14": 60,
    }

    signal = get_signal(row)

    assert signal == "Bullish trend"
    assert get_trade_direction(signal) == "long"


def test_bearish_trend_signal():
    row = {
        "Close": 80,
        "SMA_20": 90,
        "SMA_50": 100,
        "RSI_14": 40,
    }

    signal = get_signal(row)

    assert signal == "Bearish trend"
    assert get_trade_direction(signal) == "short"

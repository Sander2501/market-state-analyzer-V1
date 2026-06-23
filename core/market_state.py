import pandas as pd

from core.signals import get_signal


def analyze_market_state(data: pd.DataFrame) -> dict:
    latest = data.dropna().iloc[-1]

    close = float(latest["Close"])
    sma_20 = float(latest["SMA_20"])
    sma_50 = float(latest["SMA_50"])
    rsi = float(latest["RSI_14"])
    volatility = float(latest["Volatility_20"])

    if close > sma_20 > sma_50:
        trend = "Uptrend"
    elif close < sma_20 < sma_50:
        trend = "Downtrend"
    else:
        trend = "Ranging / unclear"

    if rsi > 70:
        momentum = "Overbought"
    elif rsi < 30:
        momentum = "Oversold"
    elif rsi > 55:
        momentum = "Bullish momentum"
    elif rsi < 45:
        momentum = "Bearish momentum"
    else:
        momentum = "Neutral momentum"

    if volatility > data["Volatility_20"].mean():
        volatility_state = "High volatility"
    else:
        volatility_state = "Normal / low volatility"

    signal = get_signal(latest)

    return {
        "close": round(close, 2),
        "trend": trend,
        "momentum": momentum,
        "rsi": round(rsi, 2),
        "volatility": volatility_state,
        "signal": signal,
    }

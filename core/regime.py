import pandas as pd

TREND_THRESHOLD_PCT = 1.0
VOLATILE_RATIO = 1.5
BREAKOUT_RATIO = 1.2


def detect_regime(data: pd.DataFrame, lookback: int = 20) -> dict:
    df = data.dropna()

    if len(df) < lookback + 1:
        return {
            "regime": "Insufficient data",
            "trend_strength_pct": None,
            "volatility_ratio": None,
            "description": "Not enough data to classify the market regime.",
        }

    close = float(df["Close"].iloc[-1])
    sma_20_now = float(df["SMA_20"].iloc[-1])
    sma_20_prev = float(df["SMA_20"].iloc[-lookback])
    sma_50_now = float(df["SMA_50"].iloc[-1])

    trend_strength = (sma_20_now - sma_20_prev) / sma_20_prev * 100

    current_vol = float(df["Volatility_20"].iloc[-1])
    median_vol = float(df["Volatility_20"].median())
    volatility_ratio = current_vol / median_vol if median_vol > 0 else 1.0

    recent_high = float(df["High"].iloc[-lookback:-1].max())
    recent_low = float(df["Low"].iloc[-lookback:-1].min())

    if close > recent_high and volatility_ratio > BREAKOUT_RATIO:
        regime = "Breakout"
        description = "Price broke above its recent range on rising volatility."
    elif close < recent_low and volatility_ratio > BREAKOUT_RATIO:
        regime = "Breakdown"
        description = "Price broke below its recent range on rising volatility."
    elif volatility_ratio > VOLATILE_RATIO and abs(trend_strength) < TREND_THRESHOLD_PCT:
        regime = "Volatile"
        description = "Volatility is elevated without a clear directional trend."
    elif trend_strength > TREND_THRESHOLD_PCT and close > sma_50_now:
        regime = "Trending Up"
        description = "The short-term average is rising and price holds above the long-term average."
    elif trend_strength < -TREND_THRESHOLD_PCT and close < sma_50_now:
        regime = "Trending Down"
        description = "The short-term average is falling and price holds below the long-term average."
    else:
        regime = "Range Bound"
        description = "Price is moving sideways within a contained range."

    return {
        "regime": regime,
        "trend_strength_pct": round(trend_strength, 2),
        "volatility_ratio": round(volatility_ratio, 2),
        "description": description,
    }

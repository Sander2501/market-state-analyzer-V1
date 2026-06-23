from core.config import RSI_BEARISH_MAX, RSI_BULLISH_MIN, RSI_OVERBOUGHT, RSI_OVERSOLD


def get_signal(row) -> str:
    if row["Close"] > row["SMA_20"] > row["SMA_50"] and RSI_BULLISH_MIN < row["RSI_14"] < RSI_OVERBOUGHT:
        return "Bullish trend"

    if row["Close"] < row["SMA_20"] < row["SMA_50"] and RSI_OVERSOLD < row["RSI_14"] < RSI_BEARISH_MAX:
        return "Bearish trend"

    if row["RSI_14"] < RSI_OVERSOLD:
        return "Oversold rebound"

    if row["RSI_14"] > RSI_OVERBOUGHT:
        return "Overbought risk"

    return "Neutral"


def get_trade_direction(signal: str) -> str:
    if signal in ["Bullish trend", "Oversold rebound"]:
        return "long"

    if signal in ["Bearish trend", "Overbought risk"]:
        return "short"

    return "none"

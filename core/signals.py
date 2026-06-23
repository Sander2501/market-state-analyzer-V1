def get_signal(row) -> str:
    if row["Close"] > row["SMA_20"] > row["SMA_50"] and 55 < row["RSI_14"] < 70:
        return "Bullish trend"

    if row["Close"] < row["SMA_20"] < row["SMA_50"] and 30 < row["RSI_14"] < 45:
        return "Bearish trend"

    if row["RSI_14"] < 30:
        return "Oversold rebound"

    if row["RSI_14"] > 70:
        return "Overbought risk"

    return "Neutral"


def get_trade_direction(signal: str) -> str:
    if signal in ["Bullish trend", "Oversold rebound"]:
        return "long"

    if signal in ["Bearish trend", "Overbought risk"]:
        return "short"

    return "none"

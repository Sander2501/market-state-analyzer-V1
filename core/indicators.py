import pandas as pd

from core.config import ATR_WINDOW, EMA_WINDOW, RSI_WINDOW, SMA_LONG_WINDOW, SMA_SHORT_WINDOW, VOLATILITY_WINDOW


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()

    df["SMA_20"] = df["Close"].rolling(window=SMA_SHORT_WINDOW).mean()
    df["SMA_50"] = df["Close"].rolling(window=SMA_LONG_WINDOW).mean()

    df["EMA_20"] = df["Close"].ewm(span=EMA_WINDOW, adjust=False).mean()

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=RSI_WINDOW).mean()
    avg_loss = loss.rolling(window=RSI_WINDOW).mean()

    rs = avg_gain / avg_loss
    df["RSI_14"] = 100 - (100 / (1 + rs))

    df["Daily_Return"] = df["Close"].pct_change()
    df["Volatility_20"] = df["Daily_Return"].rolling(window=VOLATILITY_WINDOW).std()

    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR_14"] = true_range.rolling(window=ATR_WINDOW).mean()

    return df

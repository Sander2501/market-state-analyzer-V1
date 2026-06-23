import pandas as pd


def analyze_structure(data: pd.DataFrame, window: int = 20) -> dict:
    df = data.dropna().copy()

    recent = df.tail(window)

    support = recent["Low"].min()
    resistance = recent["High"].max()
    close = recent["Close"].iloc[-1]

    distance_to_support = ((close - support) / close) * 100
    distance_to_resistance = ((resistance - close) / close) * 100

    if distance_to_support < 2:
        location = "Near support"
    elif distance_to_resistance < 2:
        location = "Near resistance"
    else:
        location = "Middle of recent range"

    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "location": location,
    }

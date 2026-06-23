import pandas as pd

from core.indicators import add_indicators


def _price_data(rows: int = 60) -> pd.DataFrame:
    values = list(range(100, 100 + rows))
    return pd.DataFrame({
        "Open": values,
        "High": [v + 2 for v in values],
        "Low": [v - 2 for v in values],
        "Close": values,
        "Volume": [1000] * rows,
    })


def test_add_indicators_adds_expected_columns():
    df = add_indicators(_price_data())

    for column in ["SMA_20", "SMA_50", "EMA_20", "RSI_14", "Daily_Return", "Volatility_20", "ATR_14"]:
        assert column in df.columns


def test_add_indicators_calculates_atr():
    df = add_indicators(_price_data())

    assert df["ATR_14"].dropna().iloc[-1] > 0

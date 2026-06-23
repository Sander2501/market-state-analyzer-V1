import pandas as pd

from core.indicators import add_indicators


def test_add_indicators_creates_expected_columns():
    data = pd.DataFrame({
        "Open": range(1, 101),
        "High": range(2, 102),
        "Low": range(0, 100),
        "Close": range(1, 101),
    })

    result = add_indicators(data)

    assert "SMA_20" in result.columns
    assert "SMA_50" in result.columns
    assert "EMA_20" in result.columns
    assert "RSI_14" in result.columns
    assert "Volatility_20" in result.columns

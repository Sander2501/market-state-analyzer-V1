import pandas as pd

from core.indicators import add_indicators
from backtesting.walk_forward import walk_forward_analysis


def _data(rows: int = 180) -> pd.DataFrame:
    closes = [100 + i for i in range(rows)]
    return add_indicators(pd.DataFrame({
        "Open": closes,
        "High": [value + 1 for value in closes],
        "Low": [value - 1 for value in closes],
        "Close": closes,
        "Volume": [1000] * rows,
    }))


def test_walk_forward_not_enough_data():
    result = walk_forward_analysis(_data(30))

    assert result["note"]
    assert result["folds"] == []


def test_walk_forward_returns_folds():
    result = walk_forward_analysis(_data())

    assert result["note"] is None
    assert result["folds"]
    assert "trades" in result["aggregate"]

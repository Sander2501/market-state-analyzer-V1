import pandas as pd

from core.indicators import add_indicators
from core.regime import detect_regime


def _data(closes: list[float]) -> pd.DataFrame:
    return add_indicators(pd.DataFrame({
        "Open": closes,
        "High": [value + 1 for value in closes],
        "Low": [value - 1 for value in closes],
        "Close": closes,
        "Volume": [1000] * len(closes),
    }))


def test_detect_regime_trending_up():
    result = detect_regime(_data(list(range(100, 180))))

    assert result["regime"] in {"Trending Up", "Breakout"}
    assert result["trend_strength_pct"] is not None


def test_detect_regime_insufficient_data():
    result = detect_regime(_data(list(range(100, 110))))

    assert result["regime"] == "Insufficient data"


def test_detect_regime_returns_description():
    result = detect_regime(_data([100 + (i % 3) for i in range(80)]))

    assert result["description"]

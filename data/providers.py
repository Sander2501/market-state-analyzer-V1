import os
from pathlib import Path

import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = Path(os.environ.get("MARKET_STATE_CACHE_DIR", PROJECT_ROOT / "cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_price_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    refresh: bool = False,
) -> pd.DataFrame:
    safe_symbol = symbol.replace("/", "_").replace("-", "_").replace("=", "_")
    cache_file = CACHE_DIR / f"{safe_symbol}_{period}_{interval}.csv"

    if cache_file.exists() and not refresh:
        return pd.read_csv(cache_file, index_col=0, parse_dates=True)

    data = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
    )

    if data.empty:
        raise ValueError(f"No data found for symbol: {symbol}")

    if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)

    data.to_csv(cache_file)

    return data



def list_cache_files() -> list[Path]:
    return sorted(CACHE_DIR.glob("*.csv"))


def clear_cache() -> int:
    removed = 0
    for cache_file in list_cache_files():
        cache_file.unlink()
        removed += 1
    return removed

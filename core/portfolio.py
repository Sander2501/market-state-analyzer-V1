import pandas as pd

from data.providers import get_price_data


def analyze_portfolio(
    symbols: list[str],
    period: str = "1y",
    interval: str = "1d",
    refresh: bool = False,
    periods_per_year: int = 252,
) -> dict:
    """Build an equal-weight portfolio and report return, volatility, and correlation."""
    returns_by_symbol = {}
    errors = {}

    for symbol in symbols:
        try:
            data = get_price_data(symbol, period=period, interval=interval, refresh=refresh)
            returns_by_symbol[symbol] = data["Close"].pct_change()
        except Exception as e:
            errors[symbol] = str(e)

    if len(returns_by_symbol) < 2:
        return {
            "symbols": list(returns_by_symbol.keys()),
            "errors": errors,
            "note": "Need at least 2 valid symbols to analyze a portfolio.",
        }

    returns_df = pd.DataFrame(returns_by_symbol).dropna()

    if returns_df.empty:
        return {
            "symbols": list(returns_by_symbol.keys()),
            "errors": errors,
            "note": "No overlapping price history across the selected symbols.",
        }

    weight = 1 / returns_df.shape[1]
    portfolio_returns = returns_df.mean(axis=1)

    annual_return = portfolio_returns.mean() * periods_per_year
    annual_volatility = portfolio_returns.std() * (periods_per_year ** 0.5)

    correlation = returns_df.corr()

    n = correlation.shape[0]
    off_diagonal = (correlation.values.sum() - n) / (n * n - n)
    diversification_score = round((1 - off_diagonal) * 100, 1)

    per_symbol_vol = {
        symbol: round(returns_df[symbol].std() * (periods_per_year ** 0.5) * 100, 2)
        for symbol in returns_df.columns
    }

    return {
        "symbols": list(returns_df.columns),
        "weight_each_pct": round(weight * 100, 2),
        "annual_return_pct": round(annual_return * 100, 2),
        "annual_volatility_pct": round(annual_volatility * 100, 2),
        "average_correlation": round(off_diagonal, 3),
        "diversification_score": diversification_score,
        "per_symbol_volatility_pct": per_symbol_vol,
        "correlation_matrix": correlation.round(2),
        "errors": errors,
        "note": None,
    }

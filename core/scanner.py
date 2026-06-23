from backtesting.engine import backtest_market_state
from core.config import SCAN_AVERAGE_RETURN_WEIGHT, SCAN_HIT_RATE_WEIGHT, SCAN_SHARPE_WEIGHT
from core.indicators import add_indicators
from core.market_state import analyze_market_state
from data.providers import get_price_data


def calculate_scan_score(signal: str, stats: dict | None) -> float:
    if signal == "Neutral" or stats is None:
        return 0

    hit_rate = stats["hit_rate"] or 0
    average_return = stats["average_return"] or 0
    sharpe_ratio = stats["sharpe_ratio"] or 0

    score = (
        hit_rate * SCAN_HIT_RATE_WEIGHT
        + average_return * SCAN_AVERAGE_RETURN_WEIGHT
        + sharpe_ratio * SCAN_SHARPE_WEIGHT
    )

    return round(score, 2)


def scan_watchlist(
    symbols: list[str],
    period: str = "1y",
    interval: str = "1d",
    holding_days: int = 10,
    transaction_cost_pct: float = 0.1,
    refresh: bool = False,
) -> list[dict]:
    results = []

    periods_per_year = 52 if interval == "1wk" else 252

    for symbol in symbols:
        try:
            data = get_price_data(
                symbol,
                period=period,
                interval=interval,
                refresh=refresh,
            )

            data = add_indicators(data)
            analysis = analyze_market_state(data)

            backtest = backtest_market_state(
                data,
                holding_days=holding_days,
                transaction_cost_pct=transaction_cost_pct,
                periods_per_year=periods_per_year,
            )

            current_signal = analysis["signal"]
            signal_stats = backtest["signals"].get(current_signal)

            score = calculate_scan_score(current_signal, signal_stats)

            results.append({
                "Symbol": symbol,
                "Score": score,
                "Close": analysis["close"],
                "Trend": analysis["trend"],
                "Regime": analysis["regime"],
                "RSI": analysis["rsi"],
                "Signal": current_signal,
                "Confidence": signal_stats["confidence"] if signal_stats else "No sample",
                "Hit Rate (%)": signal_stats["hit_rate"] if signal_stats else None,
                "Average Return (%)": signal_stats["average_return"] if signal_stats else None,
                "Sharpe Ratio": signal_stats["sharpe_ratio"] if signal_stats else None,
                "Buy & Hold (%)": backtest["benchmark"]["buy_and_hold_return"],
            })

        except Exception as e:
            results.append({
                "Symbol": symbol,
                "Score": -999,
                "Error": str(e),
            })

    return sorted(
        results,
        key=lambda row: row.get("Score", -999),
        reverse=True,
    )

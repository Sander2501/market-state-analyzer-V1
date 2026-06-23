import random

from backtesting.engine import calculate_max_drawdown


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * pct
    lower = int(k)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = k - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def monte_carlo_simulation(
    trade_returns: list[float],
    n_simulations: int = 1000,
    seed: int | None = 42,
) -> dict:
    """Resample historical trade returns to build possible equity-curve outcomes."""
    if len(trade_returns) < 2:
        return {
            "simulations": 0,
            "note": "Need at least 2 trades to run a Monte Carlo simulation.",
        }

    rng = random.Random(seed)
    n = len(trade_returns)

    final_returns = []
    max_drawdowns = []
    sample_curves = []

    for sim in range(n_simulations):
        sampled = [rng.choice(trade_returns) for _ in range(n)]

        equity = 1.0
        curve = [1.0]
        for r in sampled:
            equity *= 1 + r
            curve.append(equity)

        final_returns.append((equity - 1) * 100)
        max_drawdowns.append(calculate_max_drawdown(sampled))

        if sim < 100:
            sample_curves.append(curve)

    final_sorted = sorted(final_returns)
    drawdown_sorted = sorted(max_drawdowns)

    return {
        "simulations": n_simulations,
        "trades_per_sim": n,
        "expected_return": round(sum(final_returns) / len(final_returns), 2),
        "median_return": round(_percentile(final_sorted, 0.5), 2),
        "best_case": round(_percentile(final_sorted, 0.95), 2),
        "worst_case": round(_percentile(final_sorted, 0.05), 2),
        "worst_drawdown": round(min(max_drawdowns), 2),
        "median_drawdown": round(_percentile(drawdown_sorted, 0.5), 2),
        "probability_of_profit": round(
            sum(1 for r in final_returns if r > 0) / len(final_returns) * 100, 2
        ),
        "sample_curves": sample_curves,
        "note": None,
    }

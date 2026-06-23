import pandas as pd

from backtesting.engine import backtest_market_state


def _aggregate_trade_log(trade_log: list[dict]) -> dict:
    if not trade_log:
        return {
            "trades": 0,
            "hit_rate": None,
            "average_return": None,
            "total_return": None,
        }

    returns = [row["Return (%)"] for row in trade_log]
    wins = [r for r in returns if r > 0]

    return {
        "trades": len(returns),
        "hit_rate": round(len(wins) / len(returns) * 100, 2),
        "average_return": round(sum(returns) / len(returns), 2),
        "total_return": round(sum(returns), 2),
    }


def walk_forward_analysis(
    data: pd.DataFrame,
    n_splits: int = 4,
    holding_days: int = 10,
    transaction_cost_pct: float = 0.1,
    periods_per_year: int = 252,
) -> dict:
    """Roll forward through the data and report performance separately for
    sequential out-of-sample test windows.

    The signal rules are fixed rather than fitted. The earlier slice is retained
    as chronological context for each fold, while metrics are calculated only on
    the later test slice. This is a date split, not a parameter-optimization
    walk-forward process.
    """
    df = data.dropna().reset_index(drop=True)

    min_rows = (n_splits + 1) * (holding_days + 5)
    if len(df) < min_rows:
        return {
            "folds": [],
            "aggregate": {"trades": 0, "hit_rate": None, "average_return": None, "total_return": None},
            "note": "Not enough data for the requested number of walk-forward splits.",
        }

    fold_size = len(df) // (n_splits + 1)

    folds = []
    all_trades = []

    for i in range(1, n_splits + 1):
        train_end = fold_size * i
        test_end = fold_size * (i + 1) if i < n_splits else len(df)

        train_slice = df.iloc[:train_end]
        test_slice = df.iloc[train_end:test_end]

        if len(test_slice) <= holding_days:
            continue

        test_backtest = backtest_market_state(
            test_slice,
            holding_days=holding_days,
            transaction_cost_pct=transaction_cost_pct,
            periods_per_year=periods_per_year,
        )

        test_metrics = _aggregate_trade_log(test_backtest["trade_log"])
        all_trades.extend(test_backtest["trade_log"])

        folds.append({
            "fold": i,
            "train_rows": len(train_slice),
            "test_rows": len(test_slice),
            "test_trades": test_metrics["trades"],
            "test_hit_rate": test_metrics["hit_rate"],
            "test_average_return": test_metrics["average_return"],
            "test_total_return": test_metrics["total_return"],
        })

    return {
        "folds": folds,
        "aggregate": _aggregate_trade_log(all_trades),
        "note": None,
    }

import pandas as pd

from core.signals import get_signal, get_trade_direction


def calculate_max_drawdown(returns: list[float]) -> float:
    equity = 1
    peak = 1
    max_drawdown = 0

    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        drawdown = (equity - peak) / peak
        max_drawdown = min(max_drawdown, drawdown)

    return round(max_drawdown * 100, 2)


def calculate_sharpe_ratio(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None

    returns_series = pd.Series(returns)

    if returns_series.std() == 0:
        return None

    sharpe = returns_series.mean() / returns_series.std()

    return round(sharpe, 2)


def summarize_returns(returns: list[float]) -> dict:
    if not returns:
        return {
            "signals": 0,
            "hit_rate": None,
            "average_return": None,
            "max_drawdown": None,
            "best_trade": None,
            "worst_trade": None,
            "win_loss_ratio": None,
            "sharpe_ratio": None,
        }

    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]

    average_win = sum(wins) / len(wins) if wins else 0
    average_loss = abs(sum(losses) / len(losses)) if losses else 0

    win_loss_ratio = None
    if average_loss != 0:
        win_loss_ratio = round(average_win / average_loss, 2)

    return {
        "signals": len(returns),
        "hit_rate": round(len(wins) / len(returns) * 100, 2),
        "average_return": round(sum(returns) / len(returns) * 100, 2),
        "max_drawdown": calculate_max_drawdown(returns),
        "best_trade": round(max(returns) * 100, 2),
        "worst_trade": round(min(returns) * 100, 2),
        "win_loss_ratio": win_loss_ratio,
        "sharpe_ratio": calculate_sharpe_ratio(returns),
    }


def calculate_buy_and_hold(data: pd.DataFrame) -> float:
    df = data.dropna().copy()

    first_close = float(df["Close"].iloc[0])
    last_close = float(df["Close"].iloc[-1])

    return round(((last_close - first_close) / first_close) * 100, 2)


def backtest_market_state(
    data: pd.DataFrame,
    holding_days: int = 10,
    transaction_cost_pct: float = 0.1,
) -> dict:
    df = data.dropna().copy()
    results = {}
    trade_log = []

    i = 0

    while i < len(df) - holding_days:
        row = df.iloc[i]
        future_row = df.iloc[i + holding_days]

        signal = get_signal(row)

        if signal == "Neutral":
            i += 1
            continue

        direction = get_trade_direction(signal)

        entry_price = float(row["Close"])
        exit_price = float(future_row["Close"])

        if direction == "long":
            gross_return = (exit_price - entry_price) / entry_price
        elif direction == "short":
            gross_return = (entry_price - exit_price) / entry_price
        else:
            i += 1
            continue

        net_return = gross_return - (transaction_cost_pct / 100)

        results.setdefault(signal, []).append(net_return)

        trade_log.append({
            "Entry Date": df.index[i],
            "Exit Date": df.index[i + holding_days],
            "Signal": signal,
            "Direction": direction,
            "Entry Price": round(entry_price, 2),
            "Exit Price": round(exit_price, 2),
            "Return (%)": round(net_return * 100, 2),
        })

        i += holding_days

    return {
        "signals": {
            signal: summarize_returns(returns)
            for signal, returns in results.items()
        },
        "benchmark": {
            "buy_and_hold_return": calculate_buy_and_hold(df)
        },
        "trade_log": trade_log,
    }

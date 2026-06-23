import pandas as pd

from core.confidence import sample_confidence
from core.config import (
    DEFAULT_HOLDING_DAYS,
    DEFAULT_STOP_ATR_MULTIPLIER,
    DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER,
    DEFAULT_TRANSACTION_COST_PCT,
)
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


def calculate_sharpe_ratio(
    returns: list[float],
    holding_days: int = DEFAULT_HOLDING_DAYS,
    periods_per_year: int = 252,
) -> float | None:
    if len(returns) < 2:
        return None

    returns_series = pd.Series(returns)

    if returns_series.std() == 0:
        return None

    per_trade_sharpe = returns_series.mean() / returns_series.std()
    trades_per_year = max(periods_per_year / holding_days, 1)
    sharpe = per_trade_sharpe * (trades_per_year ** 0.5)

    return round(sharpe, 2)


def summarize_returns(
    returns: list[float],
    holding_days: int = DEFAULT_HOLDING_DAYS,
    periods_per_year: int = 252,
) -> dict:
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
            "confidence": sample_confidence(0),
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
        "sharpe_ratio": calculate_sharpe_ratio(returns, holding_days, periods_per_year),
        "confidence": sample_confidence(len(returns)),
    }


def calculate_buy_and_hold(data: pd.DataFrame) -> float:
    df = data.dropna().copy()

    first_close = float(df["Close"].iloc[0])
    last_close = float(df["Close"].iloc[-1])

    return round(((last_close - first_close) / first_close) * 100, 2)


def _risk_exit_prices(entry_price: float, atr: float, direction: str, stop_atr: float, take_profit_atr: float) -> tuple[float, float]:
    if direction == "long":
        return entry_price - stop_atr * atr, entry_price + take_profit_atr * atr
    return entry_price + stop_atr * atr, entry_price - take_profit_atr * atr


def _resolve_exit(
    future_rows: pd.DataFrame,
    entry_price: float,
    fallback_exit_price: float,
    direction: str,
    stop_price: float,
    take_profit_price: float,
) -> tuple[float, object, str]:
    for exit_date, row in future_rows.iterrows():
        high = float(row["High"])
        low = float(row["Low"])

        if direction == "long":
            stop_hit = low <= stop_price
            take_profit_hit = high >= take_profit_price
        else:
            stop_hit = high >= stop_price
            take_profit_hit = low <= take_profit_price

        if stop_hit:
            return stop_price, exit_date, "Stop loss"
        if take_profit_hit:
            return take_profit_price, exit_date, "Take profit"

    return fallback_exit_price, future_rows.index[-1], "Holding period"


def backtest_market_state(
    data: pd.DataFrame,
    holding_days: int = DEFAULT_HOLDING_DAYS,
    transaction_cost_pct: float = DEFAULT_TRANSACTION_COST_PCT,
    periods_per_year: int = 252,
    use_risk_exits: bool = False,
    stop_atr_multiplier: float = DEFAULT_STOP_ATR_MULTIPLIER,
    take_profit_atr_multiplier: float = DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER,
) -> dict:
    df = data.dropna().copy()
    results = {}
    trade_log = []

    i = 0

    while i < len(df) - holding_days:
        row = df.iloc[i]
        signal = get_signal(row)

        if signal == "Neutral":
            i += 1
            continue

        direction = get_trade_direction(signal)
        entry_price = float(row["Close"])
        future_rows = df.iloc[i + 1:i + holding_days + 1]
        fallback_exit_price = float(df.iloc[i + holding_days]["Close"])
        exit_reason = "Holding period"
        exit_index = df.index[i + holding_days]

        if direction == "none" or future_rows.empty:
            i += 1
            continue

        if use_risk_exits and "ATR_14" in row and pd.notna(row["ATR_14"]):
            stop_price, take_profit_price = _risk_exit_prices(
                entry_price,
                float(row["ATR_14"]),
                direction,
                stop_atr_multiplier,
                take_profit_atr_multiplier,
            )
            exit_price, exit_index, exit_reason = _resolve_exit(
                future_rows,
                entry_price,
                fallback_exit_price,
                direction,
                stop_price,
                take_profit_price,
            )
        else:
            exit_price = fallback_exit_price

        if direction == "long":
            gross_return = (exit_price - entry_price) / entry_price
        else:
            gross_return = (entry_price - exit_price) / entry_price

        net_return = gross_return - (transaction_cost_pct / 100)

        results.setdefault(signal, []).append(net_return)

        trade_log.append({
            "Entry Date": df.index[i],
            "Exit Date": exit_index,
            "Signal": signal,
            "Direction": direction,
            "Exit Reason": exit_reason,
            "Entry Price": round(entry_price, 2),
            "Exit Price": round(exit_price, 2),
            "Return (%)": round(net_return * 100, 2),
        })

        i += holding_days

    return {
        "signals": {
            signal: summarize_returns(returns, holding_days, periods_per_year)
            for signal, returns in results.items()
        },
        "benchmark": {
            "buy_and_hold_return": calculate_buy_and_hold(df)
        },
        "trade_log": trade_log,
    }

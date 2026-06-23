def calculate_risk_reward(entry: float, stop_loss: float, take_profit: float) -> dict:
    risk_pct = abs(entry - stop_loss) / entry * 100
    reward_pct = abs(take_profit - entry) / entry * 100
    ratio = round(reward_pct / risk_pct, 2) if risk_pct > 0 else 0.0

    return {
        "risk_pct": round(risk_pct, 2),
        "reward_pct": round(reward_pct, 2),
        "ratio": ratio,
    }


def calculate_atr_stops(
    close: float,
    atr: float,
    atr_multiplier_sl: float = 2.0,
    atr_multiplier_tp: float = 4.0,
) -> dict:
    stop_loss = round(close - atr_multiplier_sl * atr, 4)
    take_profit = round(close + atr_multiplier_tp * atr, 4)

    return {
        "atr": round(atr, 4),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
    }


def calculate_position_size(account_size: float, risk_pct: float, entry: float, stop_loss: float) -> dict:
    max_loss = account_size * (risk_pct / 100)
    price_risk = abs(entry - stop_loss)
    units = round(max_loss / price_risk, 4) if price_risk > 0 else 0.0
    position_value = round(units * entry, 2)

    return {
        "max_loss": round(max_loss, 2),
        "units": units,
        "position_value": position_value,
    }

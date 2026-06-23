def _signal_stats_line(signal: str, backtest: dict) -> str:
    stats = backtest.get("signals", {}).get(signal)
    if not stats or stats.get("hit_rate") is None:
        return (
            "There is no historical backtest sample for this exact signal in the "
            "selected period, so no win rate can be quoted."
        )

    sample_note = ""
    if stats["signals"] < 10:
        sample_note = (
            " Treat this as a small sample, so the hit rate and average return "
            "may be unstable."
        )

    return (
        f"Across {stats['signals']} similar historical occurrences in this period, "
        f"this signal showed a {stats['hit_rate']}% win rate with an average "
        f"return of {stats['average_return']}% per trade."
        f"{sample_note}"
    )


def build_facts(symbol: str, analysis: dict, structure: dict, backtest: dict) -> dict:
    """Collect the grounded numbers used by the plain-English explanation.
    Nothing here is invented; every value comes from indicators and backtests.
    """
    regime_detail = analysis.get("regime_detail", {})
    return {
        "symbol": symbol,
        "close": analysis.get("close"),
        "trend": analysis.get("trend"),
        "regime": analysis.get("regime"),
        "regime_description": regime_detail.get("description"),
        "momentum": analysis.get("momentum"),
        "rsi": analysis.get("rsi"),
        "volatility": analysis.get("volatility"),
        "signal": analysis.get("signal"),
        "location": structure.get("location"),
        "support": structure.get("support"),
        "resistance": structure.get("resistance"),
        "signal_stats_line": _signal_stats_line(analysis.get("signal"), backtest),
    }


def templated_explanation(facts: dict) -> str:
    """Deterministic, data-grounded natural-language explanation. Always works,
    no API key and no network required.
    """
    return (
        f"{facts['symbol']} is currently in a {facts['regime']} regime "
        f"({facts['trend'].lower()}), trading at {facts['close']}. "
        f"RSI is {facts['rsi']} ({facts['momentum'].lower()}), and the market is "
        f"{facts['volatility'].lower()}. Price sits {facts['location'].lower()} "
        f"(support {facts['support']}, resistance {facts['resistance']}). "
        f"The active signal is '{facts['signal']}'. {facts['signal_stats_line']} "
        f"This describes current conditions and historical analogues only; it is "
        f"not a prediction or financial advice."
    )


def explain_market_state(symbol: str, analysis: dict, structure: dict, backtest: dict) -> dict:
    """Return the deterministic market-state explanation."""
    facts = build_facts(symbol, analysis, structure, backtest)

    return {
        "templated": templated_explanation(facts),
    }

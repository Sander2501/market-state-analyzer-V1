def create_report(
    symbol: str,
    analysis: dict,
    backtest: dict,
    structure: dict | None = None,
    explanation: str | None = None,
) -> str:
    report = f"""
Market-State Report
-------------------
Symbol: {symbol}

Current Market State
- Latest close: {analysis['close']}
- Trend: {analysis['trend']}
- Momentum: {analysis['momentum']}
- Current signal: {analysis['signal']}
- RSI: {analysis['rsi']}
- Volatility: {analysis['volatility']}
"""

    if structure:
        report += f"""
Market Structure
- Support: {structure['support']}
- Resistance: {structure['resistance']}
- Location: {structure['location']}
"""

    if explanation:
        report += f"""
Signal Explanation
{explanation}
"""

    report += """
Historical Similar-State Backtest
"""

    if not backtest:
        report += "- No historical signals found for this period.\n"
    else:
        for signal_name, result in backtest.items():
            report += f"""
{signal_name}
- Signals found: {result['signals']}
- Hit rate: {result['hit_rate']}%
- Average return: {result['average_return']}%
- Max drawdown: {result['max_drawdown']}%
- Best trade: {result['best_trade']}%
- Worst trade: {result['worst_trade']}%
- Win/loss ratio: {result['win_loss_ratio']}
- Sharpe ratio: {result['sharpe_ratio']}
"""

    report += """
Interpretation
This is not financial advice and does not predict the future.
It describes the current market state and compares it with similar historical states.
"""
    return report

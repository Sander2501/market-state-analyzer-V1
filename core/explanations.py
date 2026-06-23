def explain_signal(analysis: dict, structure: dict) -> str:
    signal = analysis["signal"]

    lines = [
        f"Trend: {analysis['trend']}",
        f"Momentum: {analysis['momentum']}",
        f"Market structure: {structure['location']}",
    ]

    if signal == "Bullish trend":
        lines.append("Explanation: Price is above both moving averages and RSI shows positive momentum.")

    elif signal == "Bearish trend":
        lines.append("Explanation: Price is below both moving averages and RSI shows negative momentum.")

    elif signal == "Oversold rebound":
        lines.append("Explanation: RSI is below 30, which can indicate oversold conditions.")

    elif signal == "Overbought risk":
        lines.append("Explanation: RSI is above 70, which can indicate overbought conditions.")

    else:
        lines.append("Explanation: No strong signal is active right now.")

    return "\n".join(lines)

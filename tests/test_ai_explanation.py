from core.ai_explanation import build_facts, explain_market_state, templated_explanation


def _sample_inputs():
    analysis = {
        "close": 150.0,
        "trend": "Uptrend",
        "regime": "Trending Up",
        "regime_detail": {"description": "Short-term average is rising."},
        "momentum": "Bullish momentum",
        "rsi": 61.0,
        "volatility": "Normal / low volatility",
        "signal": "Bullish trend",
    }
    structure = {
        "location": "Middle of recent range",
        "support": 140.0,
        "resistance": 160.0,
    }
    backtest = {
        "signals": {
            "Bullish trend": {
                "signals": 12,
                "hit_rate": 58.0,
                "average_return": 2.4,
            }
        }
    }
    return analysis, structure, backtest


def test_templated_explanation_uses_real_numbers():
    analysis, structure, backtest = _sample_inputs()
    facts = build_facts("AAPL", analysis, structure, backtest)
    text = templated_explanation(facts)

    assert "AAPL" in text
    assert "Trending Up" in text
    assert "58.0% win rate" in text
    assert "not a prediction or financial advice" in text


def test_explain_market_state_is_deterministic_without_api():
    analysis, structure, backtest = _sample_inputs()

    result = explain_market_state("AAPL", analysis, structure, backtest)

    assert result["templated"]
    assert set(result) == {"templated"}


def test_missing_signal_stats_is_handled():
    analysis, structure, _ = _sample_inputs()
    facts = build_facts("AAPL", analysis, structure, {"signals": {}})

    assert "no historical backtest sample" in facts["signal_stats_line"]


def test_small_signal_sample_is_flagged():
    analysis, structure, backtest = _sample_inputs()
    backtest["signals"]["Bullish trend"]["signals"] = 2
    facts = build_facts("AAPL", analysis, structure, backtest)

    assert "small sample" in facts["signal_stats_line"].lower()

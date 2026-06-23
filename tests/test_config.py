from core.config import DEFAULT_HOLDING_DAYS, RSI_OVERBOUGHT, RSI_OVERSOLD


def test_config_exposes_strategy_defaults():
    assert DEFAULT_HOLDING_DAYS > 0
    assert RSI_OVERSOLD < RSI_OVERBOUGHT

from core.risk import calculate_atr_stops, calculate_position_size, calculate_risk_reward


def test_calculate_risk_reward():
    result = calculate_risk_reward(100, 95, 115)

    assert result["risk_pct"] == 5
    assert result["reward_pct"] == 15
    assert result["ratio"] == 3


def test_calculate_risk_reward_zero_risk():
    result = calculate_risk_reward(100, 100, 115)

    assert result["ratio"] == 0


def test_calculate_atr_stops():
    result = calculate_atr_stops(100, 2)

    assert result["stop_loss"] == 96
    assert result["take_profit"] == 108


def test_calculate_position_size():
    result = calculate_position_size(10000, 1, 100, 95)

    assert result["max_loss"] == 100
    assert result["units"] == 20
    assert result["position_value"] == 2000


def test_calculate_position_size_zero_price_risk():
    result = calculate_position_size(10000, 1, 100, 100)

    assert result["units"] == 0

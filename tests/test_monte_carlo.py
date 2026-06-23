from backtesting.monte_carlo import _percentile, monte_carlo_simulation


def test_percentile_interpolates():
    assert _percentile([0, 10], 0.5) == 5


def test_monte_carlo_requires_two_trades():
    result = monte_carlo_simulation([0.01])

    assert result["note"]


def test_monte_carlo_returns_distribution():
    result = monte_carlo_simulation([0.05, -0.02, 0.03], n_simulations=20)

    assert result["simulations"] == 20
    assert result["trades_per_sim"] == 3
    assert result["sample_curves"]

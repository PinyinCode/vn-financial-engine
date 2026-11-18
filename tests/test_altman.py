from vn_financial_engine.metrics.altman import altman_z_score


def test_altman_public_manufacturing_model_and_zone():
    result = altman_z_score(
        working_capital=300, total_assets=1000, retained_earnings=250,
        ebit=150, total_liabilities=400, sales=1200,
        market_value_equity=800, model="PUBLIC_MANUFACTURING",
    )
    assert result["status"] == "CALCULATED"
    assert result["zone"] == "SAFE"
    assert result["score"] > 2.99


def test_altman_is_not_applied_to_banks():
    result = altman_z_score(
        working_capital=10, total_assets=100, retained_earnings=10,
        ebit=5, total_liabilities=80, sales=20, market_value_equity=50,
        model="PUBLIC_MANUFACTURING", sector="BANK",
    )
    assert result["status"] == "NOT_APPLICABLE"
    assert result["score"] is None


def test_altman_missing_inputs_are_not_zero_filled():
    result = altman_z_score(
        working_capital=10, total_assets=100, retained_earnings=None,
        ebit=5, total_liabilities=80, model="NON_MANUFACTURING",
        book_value_equity=20,
    )
    assert result["status"] == "MISSING_INPUT"

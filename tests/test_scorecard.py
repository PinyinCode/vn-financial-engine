from vn_financial_engine.scoring.scorecard import (
    score_fundamentals, score_valuation, combine_score,
)


def test_bank_score_uses_asset_quality_and_capital():
    metrics = {"roe": .17, "profit_growth_yoy": .20, "npl_ratio": .015,
               "loan_loss_coverage": 1.3, "capital_adequacy": .14, "cost_to_income": .38}
    result = score_fundamentals(metrics, "BANK")
    assert result.status == "COMPLETE"
    assert result.score > 0
    assert "npl_ratio" in result.components


def test_missing_metrics_reduce_coverage_without_rescaling_available_score():
    result = score_fundamentals({"roe": .15}, "MANUFACTURING")
    assert result.coverage < 1
    assert result.components["roic"]["status"] == "MISSING"
    assert result.score < 50


def test_combined_score_reports_missing_technical_coverage():
    fund = score_fundamentals({"roe": .15}, "MANUFACTURING")
    val = score_valuation(10, 12)
    total = combine_score(fund, val, None)
    assert total.status == "PARTIAL"
    assert total.components["technical"]["score"] is None


def test_sector_models_are_not_generic_for_steel_and_technology():
    steel = score_fundamentals({
        "gross_margin": .25, "roic": .16, "net_debt_ebitda": 1.5,
        "cfo_to_net_income": 1.1, "profit_growth_yoy": .12, "inventory_days": 70,
    }, "STEEL")
    tech = score_fundamentals({
        "revenue_growth_yoy": .25, "gross_margin": .48, "roic": .17,
        "fcf_margin": .13, "cfo_to_net_income": 1.2,
    }, "TECHNOLOGY")
    assert "net_debt_ebitda" in steel.components
    assert "revenue_growth_yoy" in tech.components
    assert steel.coverage == tech.coverage == 1


def test_real_estate_model_uses_presales_and_inventory_risk():
    result = score_fundamentals({
        "roe": .12, "presales_growth_yoy": .20, "cfo_to_net_income": .8,
        "net_debt_to_equity": .7, "inventory_to_assets": .45,
    }, "REAL_ESTATE")
    assert result.status == "COMPLETE"
    assert "presales_growth_yoy" in result.components

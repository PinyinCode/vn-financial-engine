from vn_financial_engine.scoring.scorecard import score_fundamentals, score_valuation, combine_score

def test_bank_score_uses_asset_quality_and_capital():
    metrics = {"roe": .17, "profit_growth_yoy": .20, "npl_ratio": .015,
               "loan_loss_coverage": 1.3, "capital_adequacy": .14, "cost_to_income": .38}
    result = score_fundamentals(metrics, "BANK")
    assert result.status == "COMPLETE"
    assert result.score > 0
    assert "npl_quality" in result.components

def test_missing_metrics_reduce_coverage_not_fake_zero_inputs():
    result = score_fundamentals({"roe": .15}, "MANUFACTURING")
    assert result.coverage < 1
    assert result.components["profit_growth"]["status"] == "MISSING"

def test_combined_score_reports_missing_technical_coverage():
    fund = score_fundamentals({"roe": .15}, "MANUFACTURING")
    val = score_valuation(10, 12)
    total = combine_score(fund, val, None)
    assert total.status == "PARTIAL"
    assert total.components["technical"]["score"] is None

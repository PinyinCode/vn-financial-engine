from vn_financial_engine.metrics.quality import dupont_roe, piotroski_f_score


def test_dupont_components_reconcile():
    result = dupont_roe(10, 100, 50, 25)
    assert round(result["dupont_roe"], 8) == .4


def test_piotroski_reports_coverage_and_missing():
    current = {"roa": .1, "cfo": 12, "net_income": 10, "total_assets": 100,
               "long_term_debt": 20, "current_assets": 40, "current_liabilities": 20,
               "shares": 10, "gross_margin": .3, "asset_turnover": .8}
    prior = {"roa": .08, "cfo": 8, "net_income": 7, "total_assets": 95,
             "long_term_debt": 25, "current_assets": 35, "current_liabilities": 20,
             "shares": 10, "gross_margin": .25, "asset_turnover": .7}
    result = piotroski_f_score(current, prior)
    assert result["score"] == 9
    assert result["coverage"] == 1

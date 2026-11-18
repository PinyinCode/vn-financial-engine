from vn_financial_engine.metrics.sectors import calculate_sector_metrics


def test_industrial_sector_metrics_build_roic_and_leverage_ratios():
    result = calculate_sector_metrics({
        "revenue_ttm": 1000, "cogs_ttm": -700, "ebit_ttm": 150,
        "net_income_ttm": 100, "cfo_ttm": 120, "capex_ttm": -40,
        "average_total_assets": 800, "average_equity": 400,
        "effective_tax_rate": .2, "average_invested_capital": 600,
        "net_debt": 300, "ebitda_ttm": 200, "total_equity": 400,
        "inventory": 160, "total_assets": 900, "revenue_growth_yoy": .15,
        "profit_growth_yoy": .12,
    }, "STEEL")
    assert result["roic"] == .2
    assert result["net_debt_ebitda"] == 1.5
    assert result["inventory_to_assets"] == 160 / 900
    assert result["fcf_margin"] == .08


def test_bank_sector_metrics_use_bank_specific_ratios():
    result = calculate_sector_metrics({
        "net_interest_income_ttm": 80, "average_interest_earning_assets": 1000,
        "non_performing_loans": 20, "gross_loans": 1000,
        "loan_loss_reserves": 30, "capital_adequacy_ratio": .14,
        "operating_expenses_ttm": 40, "operating_income_ttm": 100,
        "net_income_ttm": 50, "average_equity": 400,
    }, "BANK")
    assert result["nim"] == .08
    assert result["npl_ratio"] == .02
    assert result["roe"] == .125

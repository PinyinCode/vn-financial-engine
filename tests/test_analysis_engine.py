from vn_financial_engine.analysis.engine import analyze_company

def test_company_analysis_keeps_score_and_valuation_separate():
    result=analyze_company(
      "FPT","TECHNOLOGY",
      {"symbol":"FPT","close":120,"eps":8,"pb":3,"pe":15,"roe":18,
       "roa":8,"profit_growth_yoy":20,"debt_to_equity":.4},
      {"cfo_to_net_income":1.1,"operating_margin":.18},
      {"pe":18,"pb":3.2},
      {"technical_score":70},
      {"primary_multiple":"PE","margin_of_safety":.25}
    )
    assert result["scores"]["max_score"]==100
    assert result["valuation"]["fair_value"] is not None
    assert result["unit_profile"].startswith("VND_PER_SHARE")

def test_ev_ebitda_primary_score_uses_enterprise_value_multiple():
    result = analyze_company(
        "HPG", "STEEL",
        {"symbol": "HPG", "close": 27, "eps": 2, "pb": 1.5, "pe": 13},
        {"roe": .14, "gross_margin": .2, "roic": .12,
         "net_debt_ebitda": 1.5, "cfo_to_net_income": 1.1,
         "profit_growth_yoy": .1, "inventory_days": 70},
        {"ev_ebitda": 6.0},
        {"technical_score": 65},
        {"primary_multiple": "EV_EBITDA", "ebitda_vnd": 10_000_000_000_000,
         "net_debt_vnd": 5_000_000_000_000, "diluted_shares": 1_000_000_000}
    )
    relative = result["valuation_score"]["components"]["relative_multiple"]["relative"]
    assert relative is not None
    assert relative > 0

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

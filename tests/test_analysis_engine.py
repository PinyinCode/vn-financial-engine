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

def test_analysis_accepts_auditable_peer_group_result():
    from vn_financial_engine.valuation.peers import build_peer_multiples

    peer_result = build_peer_multiples(
        [
            {"symbol": "AAA", "sector": "TECHNOLOGY", "pe": 14, "pb": 2.5, "ps": 2},
            {"symbol": "BBB", "sector": "TECHNOLOGY", "pe": 16, "pb": 2.8, "ps": 2.2},
            {"symbol": "CCC", "sector": "TECHNOLOGY", "pe": 18, "pb": 3.0, "ps": 2.4},
        ],
        subject_symbol="FPT", sector="TECHNOLOGY",
    )
    result = analyze_company(
        "FPT", "TECHNOLOGY",
        {"symbol": "FPT", "close": 120, "eps": 8, "pb": 3, "pe": 15,
         "roe": 18, "roa": 8, "profit_growth_yoy": 20},
        {"revenue_growth_yoy": .2, "gross_margin": .4, "roic": .15,
         "fcf_margin": .1, "cfo_to_net_income": 1.0},
        peer_result,
        {"technical_score": 70},
        {"primary_multiple": "PE"},
    )
    assert result["valuation_score"]["coverage"] == 1
    assert result["peer_comparison"]["multiples"]["pe"]["peer_count"] == 3

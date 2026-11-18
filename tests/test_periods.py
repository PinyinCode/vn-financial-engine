from vn_financial_engine.metrics.periods import standalone_quarters, trailing_twelve_months

def test_unknown_period_convention_is_not_used_for_ttm():
    rows = [{"id":"NPAT","period":f"2025-Q{i}","value":i*10,
             "period_kind":"UNKNOWN","reporting_basis":"CONSOLIDATED"} for i in range(1,5)]
    assert trailing_twelve_months(rows,"NPAT","CONSOLIDATED") is None

def test_ytd_is_converted_to_standalone_quarters():
    rows = [
      {"id":"NPAT","period":"2025-Q1","value":10,"period_kind":"YTD","reporting_basis":"CONSOLIDATED"},
      {"id":"NPAT","period":"2025-Q2","value":25,"period_kind":"YTD","reporting_basis":"CONSOLIDATED"},
      {"id":"NPAT","period":"2025-Q3","value":42,"period_kind":"YTD","reporting_basis":"CONSOLIDATED"},
      {"id":"NPAT","period":"2025-Q4","value":60,"period_kind":"ANNUAL","reporting_basis":"CONSOLIDATED"},
    ]
    quarters=standalone_quarters(rows)
    assert [r["value"] for r in quarters] == [10,15,17,18]
    ttm=trailing_twelve_months(rows,"NPAT","CONSOLIDATED")
    assert ttm["value"] == 60

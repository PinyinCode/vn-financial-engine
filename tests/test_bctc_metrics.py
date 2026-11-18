from vn_financial_engine.metrics.bctc import extract_bctc_metrics

def test_bctc_ttm_requires_verified_standalone_quarters_and_basis():
    rows=[]
    for q,v in enumerate([10,12,13,15],1):
        rows.append({"statement_type":"INCOME_STATEMENT","id":"IS_NET_REVENUE","period":f"2025-Q{q}","value":v,
                     "period_kind":"STANDALONE_QUARTER","reporting_basis":"CONSOLIDATED","unit":"VND"})
        rows.append({"statement_type":"INCOME_STATEMENT","id":"IS_COST_OF_GOODS_SOLD","period":f"2025-Q{q}","value":-v/2,
                     "period_kind":"STANDALONE_QUARTER","reporting_basis":"CONSOLIDATED"})
    result=extract_bctc_metrics(rows,"CONSOLIDATED")
    assert result["metrics"]["revenue_ttm"]==50
    assert result["metrics"]["gross_margin"]==.5

def test_bctc_unknown_period_is_not_used():
    rows=[{"id":"IS_NET_REVENUE","period":f"2025-Q{q}","value":q*10,
           "period_kind":"UNKNOWN","reporting_basis":"UNKNOWN"} for q in range(1,5)]
    result=extract_bctc_metrics(rows,"UNKNOWN")
    assert result["metrics"]["revenue_ttm"] is None

from vn_financial_engine.metrics.bctc import extract_bctc_metrics


def test_bctc_ttm_requires_verified_standalone_quarters_and_basis():
    rows=[]
    for q,v in enumerate([10,12,13,15],1):
        rows.append({"statement_type":"INCOME_STATEMENT","id":"IS_NET_REVENUE","period":f"2025-Q{q}","value":v,
                     "period_kind":"STANDALONE_QUARTER","reporting_basis":"CONSOLIDATED","unit":"VND"})
        rows.append({"statement_type":"INCOME_STATEMENT","id":"IS_COST_OF_GOODS_SOLD","period":f"2025-Q{q}","value":-v/2,
                     "period_kind":"STANDALONE_QUARTER","reporting_basis":"CONSOLIDATED","unit":"VND"})
    result=extract_bctc_metrics(rows,"CONSOLIDATED")
    assert result["metrics"]["revenue_ttm"]==50
    assert result["metrics"]["gross_margin"]==.5


def test_bctc_unknown_period_is_not_used():
    rows=[{"id":"IS_NET_REVENUE","period":f"2025-Q{q}","value":q*10,
           "period_kind":"UNKNOWN","reporting_basis":"UNKNOWN"} for q in range(1,5)]
    result=extract_bctc_metrics(rows,"UNKNOWN")
    assert result["metrics"]["revenue_ttm"] is None


def test_balance_sheet_ratios_require_verified_common_unit_and_period():
    rows = []
    for concept, value in (
        ("BS_TOTAL_ASSETS", 100),
        ("BS_OWNERS_EQUITY", 40),
        ("BS_LIABILITIES", 60),
    ):
        rows.append({
            "statement_type": "BALANCE_SHEET",
            "id": concept,
            "period": "2025-Q4",
            "value": value,
            "reporting_basis": "CONSOLIDATED",
            "unit": "VND",
        })
    result = extract_bctc_metrics(rows, "CONSOLIDATED")
    assert result["metrics"]["equity_to_assets"] == .4
    assert result["metrics"]["debt_to_equity"] == 1.5
    assert result["metric_status"]["debt_to_equity"] == "CALCULATED"


def test_balance_sheet_rejects_unknown_or_mixed_units():
    rows = [
        {"statement_type": "BALANCE_SHEET", "id": "BS_TOTAL_ASSETS",
         "period": "2025-Q4", "value": 100,
         "reporting_basis": "CONSOLIDATED", "unit": "UNKNOWN"},
        {"statement_type": "BALANCE_SHEET", "id": "BS_OWNERS_EQUITY",
         "period": "2025-Q4", "value": 40,
         "reporting_basis": "CONSOLIDATED", "unit": "VND"},
        {"statement_type": "BALANCE_SHEET", "id": "BS_LIABILITIES",
         "period": "2025-Q4", "value": 60,
         "reporting_basis": "CONSOLIDATED", "unit": "VND"},
    ]
    result = extract_bctc_metrics(rows, "CONSOLIDATED")
    assert result["metrics"]["total_assets"] is None
    assert result["metrics"]["equity_to_assets"] is None
    assert result["metrics"]["debt_to_equity"] is None
    assert result["metric_status"]["total_assets"] == "MISSING_OR_UNVERIFIED_UNIT"

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



def test_net_margin_and_cash_conversion_require_same_ttm_periods_and_units():
    rows = []
    values = {
        "IS_NET_REVENUE": [100, 110, 120, 130],
        "IS_NET_PROFIT_AFTER_TAX": [10, 11, 12, 13],
        "CF_NET_CASH_FLOWS_FROM_OPERATING_ACTIVITIES": [8, 9, 10, 11],
    }
    statements = {
        "IS_NET_REVENUE": "INCOME_STATEMENT",
        "IS_NET_PROFIT_AFTER_TAX": "INCOME_STATEMENT",
        "CF_NET_CASH_FLOWS_FROM_OPERATING_ACTIVITIES": "CASH_FLOW",
    }
    for concept, vals in values.items():
        for quarter, value in enumerate(vals, 1):
            rows.append({
                "statement_type": statements[concept], "id": concept,
                "period": f"2025-Q{quarter}", "value": value,
                "period_kind": "STANDALONE_QUARTER",
                "reporting_basis": "CONSOLIDATED", "unit": "MILLION_VND",
            })
    result = extract_bctc_metrics(rows, "CONSOLIDATED")
    assert result["metrics"]["net_margin"] == 0.1
    assert result["metrics"]["cfo_to_net_income"] == 38 / 46


def test_net_margin_rejects_different_monetary_units():
    rows = []
    for quarter in range(1, 5):
        for concept, value, unit in (
            ("IS_NET_REVENUE", 100, "MILLION_VND"),
            ("IS_NET_PROFIT_AFTER_TAX", 10, "THOUSAND_VND"),
        ):
            rows.append({
                "statement_type": "INCOME_STATEMENT", "id": concept,
                "period": f"2025-Q{quarter}", "value": value,
                "period_kind": "STANDALONE_QUARTER",
                "reporting_basis": "CONSOLIDATED", "unit": unit,
            })
    result = extract_bctc_metrics(rows, "CONSOLIDATED")
    assert result["metrics"]["net_margin"] is None
    assert result["metric_status"]["net_margin"] == "MISSING_OR_INCOMPATIBLE_TTM"

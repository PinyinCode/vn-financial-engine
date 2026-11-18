from vn_financial_engine.metrics.periods import standalone_quarters, trailing_twelve_months

def test_unknown_period_convention_is_not_used_for_ttm():
    rows = [{"id":"NPAT","period":f"2025-Q{i}","value":i*10,
             "period_kind":"UNKNOWN","reporting_basis":"CONSOLIDATED"} for i in range(1,5)]
    assert trailing_twelve_months(rows,"NPAT","CONSOLIDATED") is None

def test_ytd_is_converted_to_standalone_quarters():
    rows = [
      {"id":"NPAT","period":"2025-Q1","value":10,"period_kind":"YTD","reporting_basis":"CONSOLIDATED","unit":"VND"},
      {"id":"NPAT","period":"2025-Q2","value":25,"period_kind":"YTD","reporting_basis":"CONSOLIDATED","unit":"VND"},
      {"id":"NPAT","period":"2025-Q3","value":42,"period_kind":"YTD","reporting_basis":"CONSOLIDATED","unit":"VND"},
      {"id":"NPAT","period":"2025-Q4","value":60,"period_kind":"ANNUAL","reporting_basis":"CONSOLIDATED","unit":"VND"},
    ]
    quarters=standalone_quarters(rows)
    assert [r["value"] for r in quarters] == [10,15,17,18]
    ttm=trailing_twelve_months(rows,"NPAT","CONSOLIDATED")
    assert ttm["value"] == 60

def test_ttm_rejects_unknown_reporting_basis_even_with_standalone_quarters():
    rows = [{"id":"NPAT","period":f"2025-Q{i}","value":i*10,
             "period_kind":"STANDALONE_QUARTER","reporting_basis":"UNKNOWN"} for i in range(1,5)]
    assert trailing_twelve_months(rows,"NPAT","UNKNOWN") is None


def test_ttm_rejects_unknown_monetary_unit():
    rows = [{"statement_type": "INCOME_STATEMENT", "id": "NPAT",
             "period": f"2025-Q{q}", "value": q * 10,
             "period_kind": "STANDALONE_QUARTER",
             "reporting_basis": "CONSOLIDATED", "unit": "UNKNOWN"}
            for q in range(1, 5)]
    assert trailing_twelve_months(rows, "NPAT", "CONSOLIDATED", "INCOME_STATEMENT") is None


def test_ttm_does_not_mix_units():
    rows = []
    for quarter in range(1, 5):
        rows.append({"id": "NPAT", "period": f"2025-Q{quarter}",
                     "value": quarter * 10, "period_kind": "STANDALONE_QUARTER",
                     "reporting_basis": "CONSOLIDATED",
                     "unit": "VND" if quarter < 3 else "THOUSAND_VND"})
    assert trailing_twelve_months(rows, "NPAT", "CONSOLIDATED") is None


def test_conflicting_duplicate_period_is_excluded():
    rows = [{"statement_type": "INCOME_STATEMENT", "id": "NPAT", "period": f"2025-Q{q}", "value": q * 10,
             "period_kind": "STANDALONE_QUARTER", "reporting_basis": "CONSOLIDATED",
             "unit": "VND"} for q in range(1, 5)]
    rows.append({**rows[1], "value": 999})
    assert trailing_twelve_months(rows, "NPAT", "CONSOLIDATED") is None


def test_identical_duplicate_period_is_deduplicated():
    rows = [{"statement_type": "INCOME_STATEMENT", "id": "NPAT",
             "period": f"2025-Q{q}", "value": q * 10,
             "period_kind": "STANDALONE_QUARTER", "reporting_basis": "CONSOLIDATED",
             "unit": "VND"} for q in range(1, 5)]
    rows.append(dict(rows[0]))
    result = trailing_twelve_months(rows, "NPAT", "CONSOLIDATED", "INCOME_STATEMENT")
    assert result["value"] == 100


def test_non_finite_and_invalid_period_rows_are_ignored():
    rows = [{"id": "NPAT", "period": f"2025-Q{q}", "value": q * 10,
             "period_kind": "STANDALONE_QUARTER", "reporting_basis": "CONSOLIDATED",
             "unit": "VND"} for q in range(1, 4)]
    rows.extend([
        {"id": "NPAT", "period": "2025-Q4", "value": float("nan"),
         "period_kind": "STANDALONE_QUARTER", "reporting_basis": "CONSOLIDATED",
         "unit": "VND"},
        {"id": "NPAT", "period": "2025-Q5", "value": 40,
         "period_kind": "STANDALONE_QUARTER", "reporting_basis": "CONSOLIDATED",
         "unit": "VND"},
    ])
    assert trailing_twelve_months(rows, "NPAT", "CONSOLIDATED") is None


def test_ttm_does_not_mix_statement_types():
    rows = []
    for quarter in range(1, 5):
        rows.append({"statement_type": "INCOME_STATEMENT", "id": "NPAT",
                     "period": f"2025-Q{quarter}", "value": quarter * 10,
                     "period_kind": "STANDALONE_QUARTER",
                     "reporting_basis": "CONSOLIDATED", "unit": "VND"})
        rows.append({"statement_type": "CASH_FLOW", "id": "NPAT",
                     "period": f"2025-Q{quarter}", "value": quarter * 100,
                     "period_kind": "STANDALONE_QUARTER",
                     "reporting_basis": "CONSOLIDATED", "unit": "VND"})
    result = trailing_twelve_months(rows, "NPAT", "CONSOLIDATED", "INCOME_STATEMENT")
    assert result["value"] == 100

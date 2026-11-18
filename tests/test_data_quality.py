from vn_financial_engine.metrics.data_quality import validate_statement_data


def _balance_rows(*, assets=100, liabilities=60, equity=40, basis="CONSOLIDATED"):
    common = {
        "statement_type": "BALANCE_SHEET",
        "period": "2025-Q4",
        "period_kind": "STANDALONE_QUARTER",
        "reporting_basis": basis,
        "unit": "VND",
    }
    return [
        {**common, "id": "BS_TOTAL_ASSETS", "value": assets},
        {**common, "id": "BS_LIABILITIES", "value": liabilities},
        {**common, "id": "BS_OWNERS_EQUITY", "value": equity},
    ]


def test_data_quality_passes_balanced_verified_statement():
    result = validate_statement_data(_balance_rows())
    assert result["status"] == "PASS"
    assert result["checks"]["balance_equation_tested"] == 1
    assert result["checks"]["balance_equation_failures"] == 0


def test_data_quality_blocks_unbalanced_balance_sheet():
    result = validate_statement_data(_balance_rows(assets=100, liabilities=70, equity=40))
    assert result["status"] == "BLOCKED"
    assert result["issues"][0]["code"] == "BALANCE_SHEET_EQUATION_MISMATCH"


def test_data_quality_warns_on_unknown_source_conventions():
    rows = _balance_rows(basis="UNKNOWN")
    for row in rows:
        row["period_kind"] = "UNKNOWN"
    result = validate_statement_data(rows)
    assert result["status"] == "WARNING"
    assert result["checks"]["unknown_reporting_basis_rows"] == 3
    assert result["checks"]["unknown_period_kind_rows"] == 3


def test_data_quality_detects_conflicting_duplicate_concept():
    rows = _balance_rows()
    rows.append({**rows[0], "value": 101})
    result = validate_statement_data(rows)
    assert result["status"] == "BLOCKED"
    assert any(x["code"] == "CONFLICTING_DUPLICATE_CONCEPT" for x in result["issues"])


def test_data_quality_rejects_non_finite_values_and_bad_periods():
    rows = _balance_rows()
    rows[0]["value"] = float("nan")
    rows[1]["period"] = "2025-Q5"
    result = validate_statement_data(rows)
    codes = {x["code"] for x in result["issues"]}
    assert "INVALID_NUMERIC_VALUE" in codes
    assert "INVALID_REPORTING_PERIOD" in codes


def test_empty_statement_is_blocked():
    result = validate_statement_data([])
    assert result["status"] == "BLOCKED"
    assert result["issues"][0]["code"] == "EMPTY_STATEMENTS"

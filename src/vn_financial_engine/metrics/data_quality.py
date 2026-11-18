"""Pre-calculation quality gate for financial statement rows.

The gate is deliberately conservative: it reports missing evidence and
accounting inconsistencies without silently repairing source values.
"""
from __future__ import annotations

import math
from collections import defaultdict


VERIFIED_BASES = {"CONSOLIDATED", "PARENT_ONLY"}
VERIFIED_PERIOD_KINDS = {"STANDALONE_QUARTER", "YTD", "ANNUAL"}


def validate_statement_data(
    records: list[dict],
    *,
    balance_tolerance: float = 0.01,
) -> dict:
    """Inspect normalized BCTC rows and return issues, warnings and coverage.

    Balance equation is tested only when total assets, liabilities and equity
    are all present for the same period, reporting basis and unit.
    """
    issues: list[dict] = []
    warnings: list[dict] = []
    if not isinstance(records, list) or not records:
        return {
            "status": "BLOCKED",
            "row_count": 0,
            "valid_numeric_rows": 0,
            "coverage": 0.0,
            "checks": {},
            "issues": [{"code": "EMPTY_STATEMENTS", "message": "Không có dòng BCTC"}],
            "warnings": [],
        }

    valid_numeric = 0
    unknown_basis = 0
    unknown_period = 0
    unknown_unit = 0
    invalid_period = 0
    by_identity: dict[tuple, list[dict]] = defaultdict(list)
    by_statement: dict[tuple, list[dict]] = defaultdict(list)

    for index, row in enumerate(records):
        if not isinstance(row, dict):
            issues.append({"code": "INVALID_ROW", "row": index})
            continue

        value = row.get("value")
        try:
            numeric = float(value)
            is_numeric = math.isfinite(numeric)
        except (TypeError, ValueError):
            is_numeric = False
            numeric = None

        if is_numeric:
            valid_numeric += 1
        else:
            issues.append({
                "code": "INVALID_NUMERIC_VALUE",
                "row": index,
                "concept": row.get("id"),
            })

        basis = str(row.get("reporting_basis") or "UNKNOWN").upper()
        kind = str(row.get("period_kind") or "UNKNOWN").upper()
        period = row.get("period")
        unit = str(row.get("unit") or "UNKNOWN").upper()
        if unit in {"UNKNOWN", "NONE", "NULL", ""}:
            unknown_unit += 1
        if basis not in VERIFIED_BASES:
            unknown_basis += 1
        if kind not in VERIFIED_PERIOD_KINDS:
            unknown_period += 1
        if period:
            try:
                from .periods import quarter_index
                quarter_index(period)
            except (TypeError, ValueError):
                invalid_period += 1
                issues.append({
                    "code": "INVALID_REPORTING_PERIOD",
                    "row": index,
                    "period": period,
                })

        identity = (
            row.get("statement_type"), row.get("id"), period, basis,
            row.get("unit"),
        )
        by_identity[identity].append({**row, "_row_index": index})

        if is_numeric:
            statement_key = (
                str(row.get("statement_type") or "").upper(),
                period,
                basis,
                row.get("unit"),
            )
            by_statement[statement_key].append(row)

    duplicate_conflicts = 0
    for identity, group in by_identity.items():
        values = []
        for row in group:
            try:
                values.append(float(row.get("value")))
            except (TypeError, ValueError):
                continue
        if len(group) > 1:
            if values and any(not math.isclose(values[0], v, rel_tol=1e-9, abs_tol=1e-8)
                              for v in values[1:]):
                duplicate_conflicts += 1
                issues.append({
                    "code": "CONFLICTING_DUPLICATE_CONCEPT",
                    "statement_type": identity[0],
                    "concept": identity[1],
                    "period": identity[2],
                    "reporting_basis": identity[3],
                    "row_count": len(group),
                })
            else:
                warnings.append({
                    "code": "DUPLICATE_CONCEPT_ROWS",
                    "statement_type": identity[0],
                    "concept": identity[1],
                    "period": identity[2],
                    "row_count": len(group),
                })

    balance_checks = 0
    balance_failures = 0
    required = {
        "BS_TOTAL_ASSETS": "assets",
        "BS_LIABILITIES": "liabilities",
        "BS_OWNERS_EQUITY": "equity",
    }
    for (statement_type, period, basis, unit), rows in by_statement.items():
        if statement_type not in {"BALANCE_SHEET", "BALANCE_SHEET".upper()}:
            continue
        amounts = {}
        for row in rows:
            concept = row.get("id")
            if concept in required:
                try:
                    amounts[required[concept]] = float(row["value"])
                except (TypeError, ValueError, KeyError):
                    pass
        if len(amounts) != 3:
            continue
        balance_checks += 1
        assets = amounts["assets"]
        residual = assets - amounts["liabilities"] - amounts["equity"]
        relative_error = abs(residual) / max(abs(assets), 1.0)
        if relative_error > balance_tolerance:
            balance_failures += 1
            issues.append({
                "code": "BALANCE_SHEET_EQUATION_MISMATCH",
                "period": period,
                "reporting_basis": basis,
                "unit": unit,
                "assets": assets,
                "liabilities_plus_equity": amounts["liabilities"] + amounts["equity"],
                "residual": residual,
                "relative_error": relative_error,
            })

    if unknown_basis:
        warnings.append({"code": "UNVERIFIED_REPORTING_BASIS", "row_count": unknown_basis})
    if unknown_period:
        warnings.append({"code": "UNVERIFIED_PERIOD_KIND", "row_count": unknown_period})
    if unknown_unit:
        warnings.append({"code": "UNVERIFIED_MONETARY_UNIT", "row_count": unknown_unit})
    if invalid_period:
        warnings.append({"code": "INVALID_PERIOD_COUNT", "row_count": invalid_period})
    if not balance_checks:
        warnings.append({"code": "BALANCE_EQUATION_NOT_TESTABLE"})

    status = "BLOCKED" if issues else ("WARNING" if warnings else "PASS")
    return {
        "status": status,
        "row_count": len(records),
        "valid_numeric_rows": valid_numeric,
        "coverage": valid_numeric / len(records),
        "checks": {
            "unknown_reporting_basis_rows": unknown_basis,
            "unknown_period_kind_rows": unknown_period,
            "unknown_unit_rows": unknown_unit,
            "invalid_period_rows": invalid_period,
            "conflicting_duplicate_groups": duplicate_conflicts,
            "balance_equation_tested": balance_checks,
            "balance_equation_failures": balance_failures,
        },
        "issues": issues,
        "warnings": warnings,
    }

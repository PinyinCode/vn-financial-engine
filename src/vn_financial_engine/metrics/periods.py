"""Period-safe handling of quarterly, YTD and point-in-time statement data.

No TTM is emitted from an unknown period convention. Flow metrics require four
consecutive standalone quarters after an explicit, source-validated conversion.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict


VERIFIED_REPORTING_BASES = {"CONSOLIDATED", "PARENT_ONLY"}
VERIFIED_PERIOD_KINDS = {"STANDALONE_QUARTER", "YTD", "ANNUAL"}


def quarter_index(period: str) -> int:
    match = re.fullmatch(r"(\d{4})-Q([1-4])", str(period or ""))
    if not match:
        raise ValueError(f"Kỳ báo cáo không hợp lệ: {period!r}")
    return int(match.group(1)) * 4 + int(match.group(2)) - 1


def _finite_number(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def standalone_quarters(records: list[dict]) -> list[dict]:
    """Convert explicitly tagged YTD/annual rows into standalone quarters.

    Rows are isolated by statement, concept, reporting basis and unit. A
    conflicting duplicate for the same identity/period is excluded rather
    than silently selecting whichever source row happened to arrive last.
    """
    grouped = defaultdict(lambda: defaultdict(list))
    for row in records or []:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("period_kind", "UNKNOWN")).upper()
        period = row.get("period")
        basis = str(row.get("reporting_basis", "UNKNOWN")).upper()
        if kind not in VERIFIED_PERIOD_KINDS or basis not in VERIFIED_REPORTING_BASES:
            continue
        try:
            quarter_index(period)
        except (TypeError, ValueError):
            continue
        value = _finite_number(row.get("value"))
        if value is None:
            continue
        key = (
            str(row.get("statement_type") or "").upper(),
            row.get("id"),
            basis,
            str(row.get("unit") or "").upper(),
        )
        grouped[key][period].append({**row, "value": value})

    output = []
    for periods in grouped.values():
        # Resolve duplicates only when every numeric value agrees.
        unique_periods = {}
        for period, candidates in periods.items():
            values = [row["value"] for row in candidates]
            if any(not math.isclose(values[0], value, rel_tol=1e-9, abs_tol=1e-8)
                   for value in values[1:]):
                continue
            unique_periods[period] = candidates[0]

        for period, row in unique_periods.items():
            kind = str(row.get("period_kind")).upper()
            idx = quarter_index(period)
            quarter = idx % 4 + 1
            if kind == "STANDALONE_QUARTER":
                output.append({**row, "period_kind": "STANDALONE_QUARTER"})
                continue
            if kind == "YTD" and quarter == 1:
                output.append({**row, "period_kind": "STANDALONE_QUARTER"})
                continue

            if kind == "YTD":
                previous_period = f"{idx // 4}-Q{quarter - 1}"
            elif kind == "ANNUAL" and quarter == 4:
                previous_period = f"{idx // 4}-Q3"
            else:
                continue

            previous = unique_periods.get(previous_period)
            if previous is None or str(previous.get("period_kind", "")).upper() != "YTD":
                continue
            prior_value = _finite_number(previous.get("value"))
            current_value = _finite_number(row.get("value"))
            if prior_value is None or current_value is None:
                continue
            output.append({
                **row,
                "value": current_value - prior_value,
                "period_kind": "STANDALONE_QUARTER",
                "derived_from": [previous_period, period],
            })

    return sorted(output, key=lambda row: (quarter_index(row["period"]), str(row.get("id"))))


def trailing_twelve_months(records: list[dict], concept_id: str,
                            reporting_basis: str, statement_type: str | None = None) -> dict | None:
    basis = str(reporting_basis or "").upper()
    if basis not in VERIFIED_REPORTING_BASES:
        return None

    rows = [
        row for row in standalone_quarters(records)
        if row.get("id") == concept_id
        and str(row.get("reporting_basis") or "").upper() == basis
        and row.get("period_kind") == "STANDALONE_QUARTER"
        and str(row.get("unit") or "").strip().upper() not in {"", "UNKNOWN", "NONE", "NULL"}
        and (statement_type is None or str(row.get("statement_type") or "").upper() == statement_type.upper())
    ]
    # Different units are different financial series; never add them together.
    by_unit = defaultdict(list)
    for row in rows:
        by_unit[str(row.get("unit") or "").upper()].append(row)

    candidates = []
    for unit, unit_rows in by_unit.items():
        unit_rows.sort(key=lambda row: quarter_index(row["period"]))
        if len(unit_rows) < 4:
            continue
        last = unit_rows[-4:]
        indices = [quarter_index(row["period"]) for row in last]
        if indices != list(range(indices[0], indices[0] + 4)):
            continue
        candidates.append((unit, last))

    # Ambiguous units cannot produce a defensible TTM result.
    if len(candidates) != 1:
        return None

    unit, last = candidates[0]
    return {
        "value": sum(row["value"] for row in last),
        "periods": [row["period"] for row in last],
        "reporting_basis": basis,
        "unit": unit or None,
        "status": "CALCULATED",
    }

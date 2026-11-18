"""Period-safe handling of quarterly, YTD and point-in-time statement data.

No TTM is emitted from an unknown period convention. Flow metrics require four
consecutive standalone quarters after an explicit, source-validated conversion.
"""
from __future__ import annotations

import re
from collections import defaultdict


def quarter_index(period: str) -> int:
    match = re.fullmatch(r"(\d{4})-Q([1-4])", str(period or ""))
    if not match:
        raise ValueError(f"Kỳ báo cáo không hợp lệ: {period!r}")
    return int(match.group(1)) * 4 + int(match.group(2)) - 1


def standalone_quarters(records: list[dict]) -> list[dict]:
    """Convert explicitly tagged YTD records to standalone quarters.

    Accepted period_kind: STANDALONE_QUARTER, YTD, ANNUAL.
    ANNUAL can be used to derive Q4 only when Q1-Q3 YTD exist for same key.
    Unknown period kinds are excluded.
    """
    grouped = defaultdict(dict)
    for row in records:
        kind = str(row.get("period_kind", "UNKNOWN")).upper()
        period = row.get("period")
        if kind not in {"STANDALONE_QUARTER", "YTD", "ANNUAL"} or not period:
            continue
        key = (row.get("id"), row.get("reporting_basis", "UNKNOWN"))
        grouped[key][period] = row

    output = []
    for key, periods in grouped.items():
        for period, row in periods.items():
            kind = str(row.get("period_kind")).upper()
            value = row.get("value")
            if value is None:
                continue
            idx = quarter_index(period)
            quarter = idx % 4 + 1
            if kind == "STANDALONE_QUARTER":
                output.append({**row, "period_kind": "STANDALONE_QUARTER"})
                continue
            if kind == "YTD" and quarter == 1:
                output.append({**row, "period_kind": "STANDALONE_QUARTER"})
                continue
            if kind == "YTD":
                previous_period = f"{idx // 4}-{('Q' + str(quarter - 1))}"
                previous = periods.get(previous_period)
                if previous and str(previous.get("period_kind", "")).upper() == "YTD":
                    output.append({**row, "value": value - previous["value"],
                                   "period_kind": "STANDALONE_QUARTER",
                                   "derived_from": [previous_period, period]})
            if kind == "ANNUAL":
                previous_period = f"{idx // 4}-Q3"
                previous = periods.get(previous_period)
                if previous and previous.get("period_kind") == "YTD":
                    output.append({**row, "value": value - previous["value"],
                                   "period_kind": "STANDALONE_QUARTER",
                                   "derived_from": [previous_period, period]})
    return sorted(output, key=lambda row: quarter_index(row["period"]))


def trailing_twelve_months(records: list[dict], concept_id: str,
                            reporting_basis: str) -> dict | None:
    if str(reporting_basis or "").upper() not in {"CONSOLIDATED", "PARENT_ONLY"}:
        return None
    rows = [r for r in standalone_quarters(records)
            if r.get("id") == concept_id
            and r.get("reporting_basis") == reporting_basis
            and r.get("period_kind") == "STANDALONE_QUARTER"]
    rows.sort(key=lambda r: quarter_index(r["period"]))
    if len(rows) < 4:
        return None
    last = rows[-4:]
    indices = [quarter_index(r["period"]) for r in last]
    if indices != list(range(indices[0], indices[0] + 4)):
        return None
    return {"value": sum(r["value"] for r in last),
            "periods": [r["period"] for r in last],
            "reporting_basis": reporting_basis,
            "status": "CALCULATED"}

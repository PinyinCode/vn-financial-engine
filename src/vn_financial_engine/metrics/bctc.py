"""Period-safe extraction of common metrics from canonical BCTC statement rows."""

from __future__ import annotations

import math

from .periods import quarter_index, trailing_twelve_months


DEFAULT_CONCEPTS = {
    "revenue": "IS_NET_REVENUE",
    "cogs": "IS_COST_OF_GOODS_SOLD",
    "net_income": "IS_NET_PROFIT_AFTER_TAX",
    "cfo": "CF_NET_CASH_FLOWS_FROM_OPERATING_ACTIVITIES",
    "total_assets": "BS_TOTAL_ASSETS",
    "total_equity": "BS_OWNERS_EQUITY",
    "total_liabilities": "BS_LIABILITIES",
}

_VERIFIED_UNITS = {"VND", "THOUSAND_VND", "MILLION_VND", "BILLION_VND"}


def _latest_balance_value(
    records: list[dict], concept_id: str, reporting_basis: str
) -> tuple[float | None, str | None, str | None]:
    """Return the latest unambiguous balance value with a verified unit."""
    candidates = []
    for row in records or []:
        if not isinstance(row, dict):
            continue
        if row.get("statement_type") != "BALANCE_SHEET":
            continue
        if str(row.get("id") or "") != str(concept_id or ""):
            continue
        if str(row.get("reporting_basis") or "").upper() != str(reporting_basis).upper():
            continue
        unit = str(row.get("unit") or "").strip().upper()
        if unit not in _VERIFIED_UNITS:
            continue
        try:
            period_key = quarter_index(row.get("period"))
            value = float(row.get("value"))
        except (TypeError, ValueError, OverflowError):
            continue
        if not math.isfinite(value):
            continue
        candidates.append((period_key, row.get("period"), unit, value))

    if not candidates:
        return None, None, None
    latest_period_key = max(item[0] for item in candidates)
    latest = [item for item in candidates if item[0] == latest_period_key]
    # Multiple units or conflicting values at the latest period are ambiguous.
    identities = {(item[2], item[3]) for item in latest}
    if len(identities) != 1:
        return None, None, None
    _, period, unit, value = latest[0]
    return value, period, unit


def extract_bctc_metrics(records: list[dict], reporting_basis: str,
                         concept_map: dict | None = None) -> dict:
    """Extract TTM flows and latest point-in-time balances for one basis.

    Flow records require explicit period conventions and verified units.
    Balance-sheet values are never summed; ratios require a common period and
    monetary unit across all participating balance-sheet concepts.
    """
    concepts = {**DEFAULT_CONCEPTS, **(concept_map or {})}
    result = {"reporting_basis": reporting_basis, "metrics": {},
              "metric_status": {}, "periods": {}}
    if str(reporting_basis or "").upper() not in {"CONSOLIDATED", "PARENT_ONLY"}:
        result["status"] = "UNVERIFIED_REPORTING_BASIS"
        for key in ("revenue_ttm", "cogs_ttm", "net_income_ttm", "cfo_ttm",
                    "gross_margin", "total_assets", "total_equity",
                    "total_liabilities", "equity_to_assets", "debt_to_equity"):
            result["metrics"][key] = None
            result["metric_status"][key] = "UNVERIFIED_REPORTING_BASIS"
        return result
    result["status"] = "OK"
    flow_keys = ("revenue", "cogs", "net_income", "cfo")
    ttm = {}
    ttm_details = {}
    for key in flow_keys:
        concept_id = concepts.get(key)
        statement_type = "CASH_FLOW" if key == "cfo" else "INCOME_STATEMENT"
        value = trailing_twelve_months(
            records, concept_id, reporting_basis, statement_type
        ) if concept_id else None
        if value:
            ttm[key] = value["value"]
            ttm_details[key] = value
            result["metric_status"][f"{key}_ttm"] = "CALCULATED"
            result["periods"][f"{key}_ttm"] = value["periods"]
        else:
            ttm[key] = None
            result["metric_status"][f"{key}_ttm"] = "INSUFFICIENT_OR_UNVERIFIED_PERIODS"

    result["metrics"].update({
        "revenue_ttm": ttm["revenue"],
        "cogs_ttm": ttm["cogs"],
        "net_income_ttm": ttm["net_income"],
        "cfo_ttm": ttm["cfo"],
    })
    def compatible_ttm(left: str, right: str) -> bool:
        a, b = ttm_details.get(left), ttm_details.get(right)
        return bool(a and b and a.get("unit") == b.get("unit")
                    and a.get("periods") == b.get("periods")
                    and a.get("reporting_basis") == b.get("reporting_basis"))

    revenue, cogs = ttm["revenue"], ttm["cogs"]
    if revenue is not None and revenue > 0 and cogs is not None:
        result["metrics"]["gross_margin"] = (revenue - abs(cogs)) / revenue
        result["metric_status"]["gross_margin"] = "CALCULATED"
    else:
        result["metrics"]["gross_margin"] = None
        result["metric_status"]["gross_margin"] = "MISSING_INPUT"

    net_income = ttm["net_income"]
    if compatible_ttm("net_income", "revenue") and revenue not in (None, 0):
        result["metrics"]["net_margin"] = net_income / revenue
        result["metric_status"]["net_margin"] = "CALCULATED"
    else:
        result["metrics"]["net_margin"] = None
        result["metric_status"]["net_margin"] = "MISSING_OR_INCOMPATIBLE_TTM"

    if compatible_ttm("cfo", "net_income") and net_income not in (None, 0):
        result["metrics"]["cfo_to_net_income"] = ttm["cfo"] / net_income
        result["metric_status"]["cfo_to_net_income"] = "CALCULATED"
    else:
        result["metrics"]["cfo_to_net_income"] = None
        result["metric_status"]["cfo_to_net_income"] = "MISSING_OR_INCOMPATIBLE_TTM"

    balance = {}
    for key in ("total_assets", "total_equity", "total_liabilities"):
        value, period, unit = _latest_balance_value(
            records, concepts.get(key, ""), reporting_basis
        )
        balance[key] = {"value": value, "period": period, "unit": unit}
        result["metrics"][key] = value
        result["metric_status"][key] = (
            "CALCULATED" if value is not None else "MISSING_OR_UNVERIFIED_UNIT"
        )
        if period:
            result["periods"][key] = period

    assets = balance["total_assets"]
    equity = balance["total_equity"]
    liabilities = balance["total_liabilities"]
    snapshots = [
        (item["period"], item["unit"])
        for item in balance.values() if item["value"] is not None
    ]
    common_snapshot = (
        len(snapshots) == 3 and len(set(snapshots)) == 1
    )
    if common_snapshot:
        result["metrics"]["equity_to_assets"] = (
            equity["value"] / assets["value"]
            if assets["value"] not in (None, 0) else None
        )
        result["metrics"]["debt_to_equity"] = (
            liabilities["value"] / equity["value"]
            if equity["value"] not in (None, 0) else None
        )
        ratio_status = "CALCULATED"
    else:
        result["metrics"]["equity_to_assets"] = None
        result["metrics"]["debt_to_equity"] = None
        ratio_status = "INCOMPATIBLE_BALANCE_SNAPSHOT"
    result["metric_status"]["equity_to_assets"] = ratio_status
    result["metric_status"]["debt_to_equity"] = ratio_status
    return result

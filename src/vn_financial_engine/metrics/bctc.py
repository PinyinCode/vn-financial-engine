"""Period-safe extraction of common metrics from canonical BCTC statement rows."""

from __future__ import annotations

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


def _latest_balance_value(records: list[dict], concept_id: str,
                          reporting_basis: str) -> tuple[float | None, str | None]:
    rows = [r for r in records if r.get("id") == concept_id
            and r.get("reporting_basis") == reporting_basis
            and r.get("period")]
    if not rows:
        return None, None
    row = max(rows, key=lambda r: quarter_index(r["period"]))
    return row.get("value"), row.get("period")


def extract_bctc_metrics(records: list[dict], reporting_basis: str,
                         concept_map: dict | None = None) -> dict:
    """Extract TTM flows and latest point-in-time balances for one basis only.

    Flow records must explicitly identify STANDALONE_QUARTER, YTD or ANNUAL.
    Balance-sheet records are point-in-time and are never summed.
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
    for key in flow_keys:
        concept_id = concepts.get(key)
        statement_type = "CASH_FLOW" if key == "cfo" else "INCOME_STATEMENT"
        value = trailing_twelve_months(records, concept_id, reporting_basis, statement_type) if concept_id else None
        if value:
            ttm[key] = value["value"]
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
    revenue, cogs = ttm["revenue"], ttm["cogs"]
    if revenue is not None and revenue > 0 and cogs is not None:
        result["metrics"]["gross_margin"] = (revenue - abs(cogs)) / revenue
        result["metric_status"]["gross_margin"] = "CALCULATED"
    else:
        result["metrics"]["gross_margin"] = None
        result["metric_status"]["gross_margin"] = "MISSING_INPUT"

    for key in ("total_assets", "total_equity", "total_liabilities"):
        value, period = _latest_balance_value(records, concepts.get(key, ""), reporting_basis)
        result["metrics"][key] = value
        result["metric_status"][key] = "CALCULATED" if value is not None else "MISSING_INPUT"
        if period:
            result["periods"][key] = period

    assets, equity = result["metrics"]["total_assets"], result["metrics"]["total_equity"]
    liabilities = result["metrics"]["total_liabilities"]
    result["metrics"]["equity_to_assets"] = (
        equity / assets if equity is not None and assets not in (None, 0) else None
    )
    result["metrics"]["debt_to_equity"] = (
        liabilities / equity if liabilities is not None and equity not in (None, 0) else None
    )
    return result

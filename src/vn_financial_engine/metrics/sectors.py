"""Sector metric assembly from canonical, unit-consistent financial inputs."""

from __future__ import annotations

from .operating import bank_metrics, common_operating_metrics, securities_metrics
from .capital import return_on_invested_capital
from .quality import ratio


def calculate_sector_metrics(data: dict, sector: str) -> dict:
    """Calculate common and sector-specific ratios without filling missing values.

    All monetary inputs must share one currency and time basis. Flow metrics
    should be TTM; balance-sheet denominators should be period averages where
    the formula requires average capital/assets.
    """
    sector = str(sector or "OTHER").upper()
    common = common_operating_metrics(data)
    result = {**common}

    if sector == "BANK":
        result.update(bank_metrics(data))
        return result
    if sector == "SECURITIES":
        result.update(securities_metrics(data))
        return result

    roic = data.get("roic")
    if roic is None:
        roic = return_on_invested_capital(
            data.get("ebit_ttm"), data.get("effective_tax_rate"),
            data.get("average_invested_capital"),
        )
    result.update({
        "roic": roic,
        "revenue_growth_yoy": data.get("revenue_growth_yoy"),
        "profit_growth_yoy": data.get("profit_growth_yoy"),
        "presales_growth_yoy": data.get("presales_growth_yoy"),
        "net_debt_ebitda": ratio(data.get("net_debt"), data.get("ebitda_ttm")),
        "net_debt_to_equity": ratio(data.get("net_debt"), data.get("total_equity")),
        "inventory_to_assets": ratio(data.get("inventory"), data.get("total_assets")),
        "capex_to_cfo": ratio(
            abs(data["capex_ttm"]), data.get("cfo_ttm")
        ) if data.get("capex_ttm") is not None else None,
    })
    return result

"""Cost of capital and cash-flow valuation building blocks."""

from __future__ import annotations

from .quality import ratio


def capm_cost_of_equity(risk_free_rate: float, beta: float, equity_risk_premium: float) -> float:
    """CAPM: Ke = Rf + beta × ERP. Rates are decimals."""
    return risk_free_rate + beta * equity_risk_premium


def weighted_average_cost_of_capital(market_equity: float, interest_bearing_debt: float,
                                     cost_of_equity: float, cost_of_debt: float,
                                     tax_rate: float) -> float | None:
    """WACC using market-value capital weights and after-tax cost of debt."""
    total = market_equity + interest_bearing_debt
    if total <= 0 or market_equity < 0 or interest_bearing_debt < 0:
        return None
    if not 0 <= tax_rate <= 1:
        return None
    return (market_equity / total) * cost_of_equity + (
        interest_bearing_debt / total
    ) * cost_of_debt * (1 - tax_rate)


def invested_capital(interest_bearing_debt: float | None,
                     total_equity: float | None,
                     cash_and_equivalents: float | None) -> float | None:
    if None in (interest_bearing_debt, total_equity, cash_and_equivalents):
        return None
    return interest_bearing_debt + total_equity - cash_and_equivalents


def return_on_invested_capital(ebit: float | None, tax_rate: float | None,
                               average_invested_capital: float | None) -> float | None:
    if ebit is None or tax_rate is None or average_invested_capital in (None, 0):
        return None
    if not 0 <= tax_rate <= 1:
        return None
    return ebit * (1 - tax_rate) / average_invested_capital


def free_cash_flow_to_firm(ebit: float | None, tax_rate: float | None,
                           depreciation_amortization: float | None,
                           capex: float | None, change_in_nwc: float | None) -> float | None:
    """FCFF = EBIT(1-T) + D&A - CapEx - change in net working capital."""
    if None in (ebit, tax_rate, depreciation_amortization, capex, change_in_nwc):
        return None
    if not 0 <= tax_rate <= 1:
        return None
    return ebit * (1 - tax_rate) + depreciation_amortization - capex - change_in_nwc

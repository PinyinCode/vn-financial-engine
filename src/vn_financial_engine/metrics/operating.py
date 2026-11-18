"""Common and sector-specific operating metrics with explicit denominator rules."""

from __future__ import annotations

from .quality import ratio


def common_operating_metrics(data: dict, days: int = 365) -> dict:
    revenue = data.get("revenue_ttm")
    cogs = data.get("cogs_ttm")
    ebit = data.get("ebit_ttm")
    net_income = data.get("net_income_ttm")
    avg_assets = data.get("average_total_assets")
    avg_equity = data.get("average_equity")
    cfo = data.get("cfo_ttm")
    capex = data.get("capex_ttm")
    gross_profit = None if revenue is None or cogs is None else revenue - abs(cogs)
    fcf = None if cfo is None or capex is None else cfo - abs(capex)
    inventory_days = ratio(data.get("average_inventory"), abs(cogs)) 
    receivable_days = ratio(data.get("average_receivables"), revenue)
    payable_days = ratio(data.get("average_payables"), abs(cogs))
    return {
        "gross_margin": ratio(gross_profit, revenue),
        "operating_margin": ratio(ebit, revenue),
        "net_margin": ratio(net_income, revenue),
        "roa": ratio(net_income, avg_assets),
        "roe": ratio(net_income, avg_equity),
        "asset_turnover": ratio(revenue, avg_assets),
        "cfo_to_net_income": ratio(cfo, net_income),
        "free_cash_flow": fcf,
        "debt_to_equity": ratio(data.get("total_liabilities"), data.get("total_equity")),
        "interest_coverage": ratio(ebit, abs(data.get("interest_expense") or 0)),
        "inventory_days": None if inventory_days is None else inventory_days * days,
        "receivable_days": None if receivable_days is None else receivable_days * days,
        "payable_days": None if payable_days is None else payable_days * days,
        "cash_conversion_cycle": (
            None if None in (inventory_days, receivable_days, payable_days)
            else (inventory_days + receivable_days - payable_days) * days
        ),
    }


def bank_metrics(data: dict) -> dict:
    return {
        "nim": ratio(data.get("net_interest_income_ttm"), data.get("average_interest_earning_assets")),
        "npl_ratio": ratio(data.get("non_performing_loans"), data.get("gross_loans")),
        "loan_loss_coverage": ratio(data.get("loan_loss_reserves"), data.get("non_performing_loans")),
        "capital_adequacy": data.get("capital_adequacy_ratio"),
        "cost_to_income": ratio(data.get("operating_expenses_ttm"), data.get("operating_income_ttm")),
        "casa_ratio": ratio(data.get("current_account_deposits"), data.get("total_customer_deposits")),
        "loan_to_deposit": ratio(data.get("gross_loans"), data.get("total_customer_deposits")),
        "roe": ratio(data.get("net_income_ttm"), data.get("average_equity")),
    }


def securities_metrics(data: dict) -> dict:
    return {
        "roe": ratio(data.get("net_income_ttm"), data.get("average_equity")),
        "margin_lending_to_equity": ratio(data.get("margin_lending_balance"), data.get("equity")),
        "capital_to_assets": ratio(data.get("equity"), data.get("total_assets")),
        "operating_margin": ratio(data.get("operating_income_ttm") - data.get("operating_expenses_ttm"),
                                  data.get("operating_income_ttm"))
            if data.get("operating_income_ttm") is not None and data.get("operating_expenses_ttm") is not None
            else None,
        "proprietary_income_share": ratio(data.get("proprietary_trading_income_ttm"),
                                           data.get("operating_income_ttm")),
    }

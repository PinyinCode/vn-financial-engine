from vn_financial_engine.metrics.capital import (
    capm_cost_of_equity, weighted_average_cost_of_capital,
    return_on_invested_capital, free_cash_flow_to_firm
)
from vn_financial_engine.normalization.legacy import normalize_legacy_snapshot

def test_capm_wacc_and_roic():
    ke=capm_cost_of_equity(.04,1.1,.06)
    assert round(ke,4)==.106
    wacc=weighted_average_cost_of_capital(600,400,ke,.08,.2)
    assert round(wacc,4)==.0892
    assert round(return_on_invested_capital(100,.2,500),4)==.16

def test_fcff_formula():
    assert free_cash_flow_to_firm(100,.2,10,20,5)==65

def test_legacy_unit_conversion_is_explicit():
    row=normalize_legacy_snapshot({"symbol":"FPT","close":120,"eps":8,"pb":3,
                                   "roe":18,"roa":8,"dividend_yield":2.5,
                                   "profit_growth_yoy":20})
    assert row["price_thousand_vnd"]==120
    assert row["roe"]==.18
    assert row["profit_growth_yoy"]==.2

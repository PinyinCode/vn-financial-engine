from vn_financial_engine.valuation.models import ValuationInput
from vn_financial_engine.valuation.engine import value_company
from vn_financial_engine.valuation.income_approach import fcff_dcf_per_share


def test_graham_and_peer_valuation_are_available():
    data = ValuationInput(price=30, eps_ttm=3, bvps=20, peer_pe=12, peer_pb=1.5)
    result = value_company(data)
    assert "PE" in result.methods
    assert "PB" in result.methods
    assert "GRAHAM" in result.methods
    assert result.fair_value is not None


def test_dcf_rejects_invalid_wacc_terminal_growth():
    data = ValuationInput(price=30, fcff=2_000_000, net_debt=1_000_000,
                          diluted_shares=100_000, growth_rate=.08,
                          wacc=.07, terminal_growth=.08)
    value, reason = fcff_dcf_per_share(data)
    assert value is None
    assert reason


def test_bank_uses_residual_income_not_graham():
    data = ValuationInput(price=20, bvps=18, roe=.12, cost_of_equity=.15,
                          terminal_growth=.04, is_bank=True)
    result = value_company(data)
    assert "RESIDUAL_INCOME" in result.methods
    assert "GRAHAM" not in result.methods

from vn_financial_engine.valuation.income_approach import fcff_dcf_per_share

def test_fcff_dcf_bridges_enterprise_value_to_equity_per_share():
    data = ValuationInput(price=20, fcff=100, net_debt=100, diluted_shares=10,
                          growth_rate=.05, wacc=.10, terminal_growth=.03, forecast_years=5)
    value, reason = fcff_dcf_per_share(data)
    assert reason is None
    assert value is not None and value > 0

def test_bank_valuation_excludes_industrial_methods_even_if_inputs_exist():
    data = ValuationInput(
        price=20, eps_ttm=2, bvps=18, ebitda=100, net_debt=20,
        diluted_shares=10, peer_pe=10, peer_pb=1.2, peer_ev_ebitda=5,
        is_bank=True,
    )
    result = value_company(data)
    assert "PE" in result.methods and "PB" in result.methods
    assert "EV_EBITDA" not in result.methods
    assert "FCFF_DCF" not in result.methods
    assert "GRAHAM" not in result.methods


def test_technology_valuation_excludes_pb_and_graham():
    data = ValuationInput(
        price=30, eps_ttm=3, bvps=20, revenue_per_share=15,
        peer_pe=15, peer_pb=2, peer_ps=3, sector="TECHNOLOGY",
    )
    result = value_company(data)
    assert "PE" in result.methods
    assert "PS" in result.methods
    assert "PB" not in result.methods
    assert "GRAHAM" not in result.methods


def test_real_estate_nav_is_explicitly_not_implemented():
    data = ValuationInput(price=20, bvps=18, peer_pb=1.1, sector="REAL_ESTATE")
    result = value_company(data)
    assert "PB" in result.methods
    assert "NAV" in result.excluded_methods

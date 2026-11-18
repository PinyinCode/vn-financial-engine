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
    data = ValuationInput(price=20, bvps=18, growth_rate=.12, cost_of_equity=.15,
                          terminal_growth=.04, is_bank=True)
    result = value_company(data)
    assert "RESIDUAL_INCOME" in result.methods
    assert "GRAHAM" not in result.methods

from vn_financial_engine.metrics.operating import common_operating_metrics, securities_metrics
from vn_financial_engine.technical.analyzer import ProfessionalTechnicalAnalyzer


def test_operating_metrics_tolerate_missing_cogs_and_interest_expense():
    result = common_operating_metrics({"revenue_ttm": 100, "ebit_ttm": 20})
    assert result["gross_margin"] is None
    assert result["inventory_days"] is None
    assert result["interest_coverage"] is None
    assert result["operating_margin"] == .2


def test_fcf_margin_is_calculated_only_with_required_inputs():
    result = common_operating_metrics({
        "revenue_ttm": 100, "cfo_ttm": 30, "capex_ttm": 10,
    })
    assert result["free_cash_flow"] == 20
    assert result["fcf_margin"] == .2


def test_securities_metrics_handle_partial_statement_inputs():
    result = securities_metrics({"equity": 100, "total_assets": 200})
    assert result["capital_to_assets"] == .5
    assert result["operating_margin"] is None


def test_technical_insufficient_history_is_missing_not_zero():
    result = ProfessionalTechnicalAnalyzer([]).analyze()
    assert result["technical_score"] is None
    assert result["technical_status"] == "Chưa đủ dữ liệu lịch sử"

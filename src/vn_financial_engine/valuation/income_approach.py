"""Income-approach valuations: FCFF DCF, Gordon DDM and residual income."""

from __future__ import annotations

from .models import ValuationInput


def fcff_dcf_per_share(data: ValuationInput) -> tuple[float | None, str | None]:
    """Enterprise FCFF DCF, bridged to equity value per diluted share.

    FCFF is discounted at WACC to obtain enterprise value. Net debt is then
    deducted and the result divided by diluted shares. All monetary inputs
    must use the same currency unit.
    """
    fcff, g, wacc, tg = data.fcff, data.growth_rate, data.wacc, data.terminal_growth
    years = data.forecast_years
    if fcff is None or fcff <= 0:
        return None, "FCFF doanh nghiệp thiếu hoặc không dương"
    if data.net_debt is None or data.diluted_shares is None or data.diluted_shares <= 0:
        return None, "Thiếu nợ ròng hoặc số cổ phiếu pha loãng"
    if g is None or wacc is None or tg is None:
        return None, "Thiếu giả định tăng trưởng, WACC hoặc tăng trưởng dài hạn"
    if years < 1 or wacc <= tg or wacc <= -1 or tg < -0.02 or tg >= 0.08 or g <= -0.5 or g >= 0.5:
        return None, "Giả định DCF không hợp lệ (cần WACC > terminal growth)"
    projected = [fcff * (1 + g) ** year for year in range(1, years + 1)]
    pv_explicit = sum(value / (1 + wacc) ** year for year, value in enumerate(projected, 1))
    terminal = projected[-1] * (1 + tg) / (wacc - tg)
    pv_terminal = terminal / (1 + wacc) ** years
    equity_value = pv_explicit + pv_terminal - data.net_debt
    per_share = equity_value / data.diluted_shares
    if per_share <= 0:
        return None, "Giá trị vốn chủ sau khi trừ nợ ròng không dương"
    return per_share, None


def gordon_ddm_per_share(data: ValuationInput) -> tuple[float | None, str | None]:
    d1 = data.dividend_per_share
    ke, g = data.cost_of_equity, data.terminal_growth
    if d1 is None or d1 <= 0 or ke is None or g is None:
        return None, "Thiếu cổ tức dự kiến hoặc cost of equity"
    if ke <= g or ke <= 0:
        return None, "Cost of equity phải lớn hơn tăng trưởng dài hạn"
    return d1 / (ke - g), None


def residual_income_bank_per_share(data: ValuationInput) -> tuple[float | None, str | None]:
    """Single-stage residual-income model: BVPS + (ROE-ke)*BVPS/(ke-g)."""
    bvps, roe, ke, g = data.bvps, data.growth_rate, data.cost_of_equity, data.terminal_growth
    if not data.is_bank:
        return None, "Residual income chỉ bật cho ngân hàng trong cấu hình hiện tại"
    if bvps is None or bvps <= 0 or roe is None or ke is None or g is None:
        return None, "Thiếu BVPS, ROE, cost of equity hoặc tăng trưởng dài hạn"
    if ke <= g or ke <= 0:
        return None, "Cost of equity phải lớn hơn tăng trưởng dài hạn"
    return bvps + ((roe - ke) * bvps / (ke - g)), None

"""Income-approach valuations: FCFF DCF, Gordon DDM and residual income."""

from __future__ import annotations

from .models import ValuationInput


def fcff_dcf_per_share(data: ValuationInput) -> tuple[float | None, str | None]:
    """Simplified per-share FCFF DCF; requires normalized FCF/share and explicit WACC."""
    fcf = data.free_cash_flow_per_share
    g = data.growth_rate
    wacc = data.wacc
    tg = data.terminal_growth
    years = data.forecast_years
    if fcf is None or fcf <= 0:
        return None, "FCF trên cổ phiếu thiếu hoặc không dương"
    if g is None or wacc is None or tg is None:
        return None, "Thiếu giả định tăng trưởng, WACC hoặc tăng trưởng dài hạn"
    if years < 1 or wacc <= tg or tg < -0.02 or tg >= 0.08 or g <= -0.5 or g >= 0.5:
        return None, "Giả định DCF không hợp lệ (cần WACC > terminal growth)"
    projected = [fcf * (1 + g) ** year for year in range(1, years + 1)]
    pv_explicit = sum(value / (1 + wacc) ** year for year, value in enumerate(projected, 1))
    terminal = projected[-1] * (1 + tg) / (wacc - tg)
    pv_terminal = terminal / (1 + wacc) ** years
    return pv_explicit + pv_terminal, None


def gordon_ddm_per_share(data: ValuationInput) -> tuple[float | None, str | None]:
    d1 = data.dividend_per_share
    ke, g = data.cost_of_equity, data.terminal_growth
    if d1 is None or d1 <= 0 or ke is None or g is None:
        return None, "Thiếu cổ tức dự kiến hoặc cost of equity"
    if ke <= g or ke <= 0:
        return None, "Cost of equity phải lớn hơn tăng trưởng dài hạn"
    return d1 / (ke - g), None


def residual_income_bank_per_share(data: ValuationInput) -> tuple[float | None, str | None]:
    """Single-stage residual-income model for banks: BVPS + (ROE-ke)*BVPS/(ke-g)."""
    bvps, roe, ke, g = data.bvps, data.growth_rate, data.cost_of_equity, data.terminal_growth
    if not data.is_bank:
        return None, "Residual income cấu hình trong engine này chỉ bật cho ngân hàng"
    if bvps is None or bvps <= 0 or roe is None or ke is None or g is None:
        return None, "Thiếu BVPS, ROE, cost of equity hoặc tăng trưởng dài hạn"
    if ke <= g or ke <= 0:
        return None, "Cost of equity phải lớn hơn tăng trưởng dài hạn"
    return bvps + ((roe - ke) * bvps / (ke - g)), None

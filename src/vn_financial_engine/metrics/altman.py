"""Altman Z-score variants; do not apply financial-sector models mechanically."""

from __future__ import annotations


def altman_z_score(
    *,
    working_capital: float | None,
    total_assets: float | None,
    retained_earnings: float | None,
    ebit: float | None,
    total_liabilities: float | None,
    sales: float | None = None,
    market_value_equity: float | None = None,
    book_value_equity: float | None = None,
    model: str = "PUBLIC_MANUFACTURING",
    sector: str = "OTHER",
) -> dict:
    """Calculate a named Altman model and return its original zone classification.

    PUBLIC_MANUFACTURING: original public manufacturing Z model.
    NON_MANUFACTURING: Z'' variant using book equity/liabilities.

    Classic cutoffs were developed on historical US samples. Treat the zone as
    a screening signal, not a calibrated default probability for Vietnamese
    issuers. Banks and other financial institutions are excluded.
    """
    if str(sector).upper() in {"BANK", "SECURITIES", "FINANCIAL"}:
        return {"score": None, "model": model, "status": "NOT_APPLICABLE",
                "reason": "Altman Z-score không áp dụng máy móc cho định chế tài chính"}
    if total_assets is None or total_assets <= 0:
        return {"score": None, "model": model, "status": "MISSING_INPUT",
                "reason": "Thiếu tổng tài sản dương"}

    x1 = None if working_capital is None else working_capital / total_assets
    x2 = None if retained_earnings is None else retained_earnings / total_assets
    x3 = None if ebit is None else ebit / total_assets

    model = str(model).upper()
    if model == "PUBLIC_MANUFACTURING":
        if None in (x1, x2, x3, sales, market_value_equity) or not total_liabilities:
            return {"score": None, "model": model, "status": "MISSING_INPUT",
                    "reason": "Thiếu đầu vào của mô hình doanh nghiệp sản xuất niêm yết"}
        x4 = market_value_equity / total_liabilities
        x5 = sales / total_assets
        score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + .6 * x4 + 1.0 * x5
        zone = "SAFE" if score > 2.99 else "DISTRESS" if score < 1.81 else "GREY"
    elif model == "NON_MANUFACTURING":
        if None in (x1, x2, x3, book_value_equity) or not total_liabilities:
            return {"score": None, "model": model, "status": "MISSING_INPUT",
                    "reason": "Thiếu đầu vào của mô hình Z'' phi sản xuất"}
        x4 = book_value_equity / total_liabilities
        score = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
        zone = "SAFE" if score > 2.6 else "DISTRESS" if score < 1.1 else "GREY"
    else:
        raise ValueError("model phải là PUBLIC_MANUFACTURING hoặc NON_MANUFACTURING")

    return {
        "score": round(score, 4),
        "model": model,
        "zone": zone,
        "status": "CALCULATED",
        "cutoff_note": "Ngưỡng gốc Altman; cần hiệu chỉnh trước khi dùng như xác suất vỡ nợ tại Việt Nam",
        "components": {"x1_working_capital_assets": x1,
                       "x2_retained_earnings_assets": x2,
                       "x3_ebit_assets": x3,
                       "x4_equity_liabilities": x4},
    }

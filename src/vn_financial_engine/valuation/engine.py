"""Sector-constrained multi-method valuation with explicit exclusions."""

from __future__ import annotations

from .income_approach import (
    fcff_dcf_per_share, gordon_ddm_per_share, residual_income_bank_per_share,
)
from .models import ValuationInput, ValuationResult
from .multiples import calculate_multiples


SECTOR_METHODS = {
    "BANK": {"PE", "PB", "GORDON_DDM", "RESIDUAL_INCOME"},
    "SECURITIES": {"PE", "PB", "GORDON_DDM"},
    "STEEL": {"PE", "PB", "EV_EBITDA", "FCFF_DCF"},
    "FERTILIZER": {"PE", "PB", "EV_EBITDA", "FCFF_DCF"},
    "OIL_GAS": {"PE", "PB", "EV_EBITDA", "FCFF_DCF"},
    "MANUFACTURING": {"PE", "PB", "EV_EBITDA", "FCFF_DCF"},
    "TECHNOLOGY": {"PE", "PS", "EV_EBITDA", "FCFF_DCF"},
    "REAL_ESTATE": {"PE", "PB"},
}


def _weighted_quantile(items: list[tuple[float, float]], quantile: float) -> float:
    ordered = sorted(items)
    total = sum(weight for _, weight in ordered)
    threshold = total * quantile
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


def value_company(data: ValuationInput, margin_of_safety: float = 0.25) -> ValuationResult:
    if not 0 <= margin_of_safety < 0.8:
        raise ValueError("margin_of_safety must be in [0, 0.8)")

    sector = "BANK" if data.is_bank else str(data.sector or "OTHER").upper()
    allowed = set(data.allowed_methods) if data.allowed_methods is not None else SECTOR_METHODS.get(
        sector, {"PE", "PB", "PS", "EV_EBITDA", "GRAHAM", "FCFF_DCF", "GORDON_DDM"}
    )
    methods, excluded = calculate_multiples(data, allowed)
    weights = {name: 1.0 for name in methods}

    income_methods = (
        ("FCFF_DCF", fcff_dcf_per_share),
        ("GORDON_DDM", gordon_ddm_per_share),
        ("RESIDUAL_INCOME", residual_income_bank_per_share),
    )
    for name, function in income_methods:
        if name not in allowed:
            excluded[name] = "Phương pháp không nằm trong cấu hình ngành"
            continue
        value, reason = function(data)
        if value is not None and value > 0:
            methods[name] = value
            weights[name] = 2.0 if name in {"FCFF_DCF", "RESIDUAL_INCOME"} else 1.0
        else:
            excluded[name] = reason or "Không tính được"

    if sector == "REAL_ESTATE":
        excluded["NAV"] = (
            "Chưa bật NAV: cần dữ liệu dự án, pháp lý, tiến độ, presales, "
            "chi phí còn lại và nợ phân bổ theo dự án"
        )

    if not methods:
        return ValuationResult(excluded_methods=excluded, status="INSUFFICIENT_DATA")

    weighted = [(value, weights[name]) for name, value in methods.items()]
    fair = _weighted_quantile(weighted, 0.50)
    low = _weighted_quantile(weighted, 0.25)
    high = _weighted_quantile(weighted, 0.75)
    buy_below = fair * (1 - margin_of_safety)
    mos = (fair - data.price) / fair if fair > 0 and data.price > 0 else None
    upside = fair / data.price - 1 if data.price > 0 else None

    return ValuationResult(
        methods=methods,
        method_weights=weights,
        fair_value=round(fair, 4),
        fair_value_low=round(low, 4),
        fair_value_high=round(high, 4),
        buy_below=round(buy_below, 4),
        margin_of_safety=mos,
        upside_to_fair_value=upside,
        status="ESTIMATE" if len(methods) >= 2 else "SINGLE_METHOD",
        excluded_methods=excluded,
        assumptions={
            "margin_of_safety": margin_of_safety,
            "aggregation": "weighted_median",
            "range": "weighted_25th_to_75th_percentile",
            "sector": sector,
            "eligible_methods": sorted(allowed),
        },
    )

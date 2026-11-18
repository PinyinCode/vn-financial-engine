"""Multi-method valuation aggregator with explicit exclusions and assumptions."""

from __future__ import annotations

from .income_approach import fcff_dcf_per_share, gordon_ddm_per_share, residual_income_bank_per_share
from .models import ValuationInput, ValuationResult
from .multiples import calculate_multiples


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
    methods, excluded = calculate_multiples(data)
    weights = {name: 1.0 for name in methods}
    for name, fn in (
        ("FCFF_DCF", fcff_dcf_per_share),
        ("GORDON_DDM", gordon_ddm_per_share),
        ("RESIDUAL_INCOME", residual_income_bank_per_share),
    ):
        value, reason = fn(data)
        if value is not None and value > 0:
            methods[name] = value
            weights[name] = 2.0 if name in ("FCFF_DCF", "RESIDUAL_INCOME") else 1.0
        else:
            excluded[name] = reason or "Không tính được"

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
        methods=methods, method_weights=weights, fair_value=round(fair, 4),
        fair_value_low=round(low, 4), fair_value_high=round(high, 4),
        buy_below=round(buy_below, 4), margin_of_safety=mos,
        upside_to_fair_value=upside,
        status="ESTIMATE" if len(methods) >= 2 else "SINGLE_METHOD",
        excluded_methods=excluded,
        assumptions={"margin_of_safety": margin_of_safety,
                     "aggregation": "weighted_median",
                     "range": "weighted_25th_to_75th_percentile"},
    )

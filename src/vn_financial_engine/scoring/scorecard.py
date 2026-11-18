"""Sector-aware, auditable scorecards.

All ratio inputs are decimals unless the metric is explicitly a multiple, days,
or currency amount. Weights sum to 50 fundamental points per sector. Missing
metrics remain missing and reduce coverage; they are never coerced to zero.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    score: float
    max_score: float
    coverage: float
    components: dict[str, dict]
    status: str


def _higher(value, bands):
    if value is None:
        return None
    for threshold, points in bands:
        if value >= threshold:
            return points
    return 0.0


def _lower(value, bands):
    if value is None:
        return None
    for ceiling, points in bands:
        if value <= ceiling:
            return points
    return 0.0


def _score(items):
    components, earned, available_weight = {}, 0.0, 0.0
    total_weight = sum(weight for _, weight, _, _ in items)
    for name, weight, value, normalized_points in items:
        if normalized_points is None:
            components[name] = {
                "score": None, "max": weight, "value": value, "status": "MISSING"
            }
            continue
        earned += normalized_points * weight
        available_weight += weight
        components[name] = {
            "score": round(normalized_points * weight, 2),
            "max": weight,
            "value": value,
            "status": "AVAILABLE",
        }
    coverage = available_weight / total_weight if total_weight else 0.0
    # Keep score on the full 50-point scale. Missing evidence does not inflate
    # the result by rescaling a tiny observed subset to 50.
    score = earned
    return ScoreResult(
        round(score, 2), 50, round(coverage, 3), components,
        "COMPLETE" if coverage >= .9 else "PARTIAL",
    )


def _higher_item(metrics, name, weight, bands):
    value = metrics.get(name)
    return name, weight, value, _higher(value, bands)


def _lower_item(metrics, name, weight, bands):
    value = metrics.get(name)
    return name, weight, value, _lower(value, bands)


def score_fundamentals(metrics, sector):
    """Score fundamentals with distinct financial-sector and operating-sector models."""
    m = metrics or {}
    sector = str(sector or "OTHER").upper()
    high_growth = [(0.30, 1), (0.20, .8), (.10, .6), (0, .3)]
    normal_growth = [(.25, 1), (.15, .8), (.05, .6), (0, .3)]
    roe_bands = [(.20, 1), (.15, .8), (.10, .6), (.05, .3)]
    cash_bands = [(1, 1), (.8, .8), (.5, .6), (0, .3)]
    low_leverage = [(.5, 1), (1, .8), (1.5, .6), (2.5, .3)]
    high_roic = [(.18, 1), (.14, .8), (.10, .6), (.05, .3)]
    high_margin = [(.35, 1), (.25, .8), (.15, .6), (.05, .3)]
    low_debt_ebitda = [(0, 1), (1, .9), (2, .7), (3, .4), (4, .2)]

    if sector == "BANK":
        specs = [
            _higher_item(m, "roe", 12, roe_bands),
            _higher_item(m, "profit_growth_yoy", 8, normal_growth),
            _lower_item(m, "npl_ratio", 8, [(.01, 1), (.02, .8), (.03, .6), (.05, .3)]),
            _higher_item(m, "loan_loss_coverage", 6, [(1.5, 1), (1.2, .8), (1, .6), (.7, .3)]),
            _higher_item(m, "capital_adequacy", 10, [(.15, 1), (.12, .8), (.10, .6), (.08, .3)]),
            _lower_item(m, "cost_to_income", 6, [(.30, 1), (.40, .8), (.50, .6), (.60, .3)]),
        ]
    elif sector == "SECURITIES":
        specs = [
            _higher_item(m, "roe", 10, roe_bands),
            _higher_item(m, "profit_growth_yoy", 8, high_growth),
            _higher_item(m, "capital_to_assets", 10, [(.50, 1), (.35, .8), (.25, .6), (.15, .3)]),
            _lower_item(m, "margin_lending_to_equity", 10, [(1, 1), (1.5, .8), (2, .5), (2.5, .2)]),
            _higher_item(m, "operating_margin", 12, high_margin),
        ]
    elif sector in {"STEEL", "FERTILIZER"}:
        specs = [
            _higher_item(m, "gross_margin", 10, [(.30, 1), (.22, .8), (.15, .6), (.08, .3)]),
            _higher_item(m, "roic", 10, high_roic),
            _lower_item(m, "net_debt_ebitda", 10, low_debt_ebitda),
            _higher_item(m, "cfo_to_net_income", 8, cash_bands),
            _higher_item(m, "profit_growth_yoy", 6, normal_growth),
            _lower_item(m, "inventory_days", 6, [(45, 1), (75, .8), (110, .6), (160, .3)]),
        ]
    elif sector == "TECHNOLOGY":
        specs = [
            _higher_item(m, "revenue_growth_yoy", 12, high_growth),
            _higher_item(m, "gross_margin", 10, [(.50, 1), (.40, .8), (.30, .6), (.20, .3)]),
            _higher_item(m, "roic", 10, high_roic),
            _higher_item(m, "fcf_margin", 10, [(.18, 1), (.12, .8), (.06, .6), (0, .3)]),
            _higher_item(m, "cfo_to_net_income", 8, cash_bands),
        ]
    elif sector == "OIL_GAS":
        specs = [
            _higher_item(m, "roic", 12, high_roic),
            _lower_item(m, "net_debt_ebitda", 12, low_debt_ebitda),
            _higher_item(m, "interest_coverage", 10, [(8, 1), (5, .8), (3, .6), (1.5, .3)]),
            _higher_item(m, "cfo_to_net_income", 8, cash_bands),
            _higher_item(m, "profit_growth_yoy", 8, normal_growth),
        ]
    elif sector == "REAL_ESTATE":
        specs = [
            _higher_item(m, "roe", 8, roe_bands),
            _higher_item(m, "presales_growth_yoy", 10, high_growth),
            _higher_item(m, "cfo_to_net_income", 10, cash_bands),
            _lower_item(m, "net_debt_to_equity", 12, low_leverage),
            _lower_item(m, "inventory_to_assets", 10, [(.25, 1), (.40, .8), (.55, .6), (.70, .3)]),
        ]
    elif sector == "MANUFACTURING":
        specs = [
            _higher_item(m, "roe", 10, roe_bands),
            _higher_item(m, "roic", 10, high_roic),
            _higher_item(m, "cfo_to_net_income", 10, cash_bands),
            _lower_item(m, "debt_to_equity", 10, low_leverage),
            _higher_item(m, "interest_coverage", 10, [(8, 1), (5, .8), (3, .6), (1.5, .3)]),
        ]
    else:
        specs = [
            _higher_item(m, "roe", 12, roe_bands),
            _higher_item(m, "profit_growth_yoy", 10, normal_growth),
            _higher_item(m, "cfo_to_net_income", 10, cash_bands),
            _lower_item(m, "debt_to_equity", 10, low_leverage),
            _higher_item(m, "operating_margin", 8, high_margin),
        ]
    return _score(specs)


def score_valuation(current_multiple, peer_multiple):
    if (current_multiple is None or peer_multiple is None
            or current_multiple <= 0 or peer_multiple <= 0):
        return ScoreResult(
            0, 30, 0,
            {"relative_multiple": {"score": None, "max": 30, "status": "MISSING"}},
            "INSUFFICIENT_DATA",
        )
    relative = current_multiple / peer_multiple
    points = (
        30 if relative <= .70 else
        26 if relative <= .85 else
        22 if relative <= 1 else
        16 if relative <= 1.15 else
        9 if relative <= 1.35 else 3
    )
    return ScoreResult(
        points, 30, 1,
        {"relative_multiple": {"score": points, "max": 30,
                               "relative": round(relative, 4), "status": "AVAILABLE"}},
        "COMPLETE",
    )


def combine_score(fundamental, valuation, technical_score_100):
    tech = None if technical_score_100 is None else max(0, min(100, technical_score_100)) * .2
    parts = {
        "fundamental": {"score": fundamental.score, "max": 50,
                        "coverage": fundamental.coverage},
        "valuation": {"score": valuation.score, "max": 30,
                      "coverage": valuation.coverage},
        "technical": {"score": tech, "max": 20,
                      "status": "MISSING" if tech is None else "AVAILABLE"},
    }
    total = fundamental.score + valuation.score + (tech or 0)
    coverage = (
        fundamental.coverage * 50 + valuation.coverage * 30
        + (20 if tech is not None else 0)
    ) / 100
    return ScoreResult(
        round(total, 2), 100, round(coverage, 3), parts,
        "COMPLETE" if coverage >= .9 else "PARTIAL",
    )

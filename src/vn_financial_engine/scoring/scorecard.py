"""Transparent, sector-aware scoring. Missing data is not treated as a zero value."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    score: float
    max_score: float
    coverage: float
    components: dict[str, dict]
    status: str


def _band(value: float | None, bands: list[tuple[float, float]]) -> float | None:
    if value is None:
        return None
    for threshold, points in bands:
        if value >= threshold:
            return points
    return 0.0


def score_fundamentals(metrics: dict, sector: str) -> ScoreResult:
    """Fundamental score out of 50; weights differ by business model."""
    bank = sector == "BANK"
    securities = sector == "SECURITIES"
    weights = {
        "profitability": 15 if not bank else 12,
        "growth": 10,
        "cash_conversion": 8 if not bank and not securities else 4,
        "balance_sheet": 9 if not bank and not securities else 12,
        "capital_quality": 8 if bank else 3,
    }
    definitions = {
        "profitability": ("roe", [(0.20, 15), (0.15, 12), (0.10, 8), (0.05, 4)]),
        "growth": ("profit_growth_yoy", [(0.25, 10), (0.15, 8), (0.05, 6), (0.0, 3)]),
        "cash_conversion": ("cfo_to_net_income", [(1.0, 8), (0.8, 6), (0.5, 3), (0.0, 1)]),
        "balance_sheet": ("equity_to_assets", [(0.30, 9), (0.20, 7), (0.10, 4), (0.0, 2)]),
        "capital_quality": ("capital_adequacy", [(0.15, 8), (0.12, 6), (0.10, 4), (0.08, 2)]),
    }
    components = {}
    earned = possible = 0.0
    for name, weight in weights.items():
        metric_key, bands = definitions[name]
        value = metrics.get(metric_key)
        points = _band(value, bands)
        if points is None:
            components[name] = {"score": None, "max": weight, "input": metric_key, "status": "MISSING"}
            continue
        # Scale generic bands to the configured component weight.
        base_max = max(p for _, p in bands)
        scaled = points * weight / base_max
        earned += scaled
        possible += weight
        components[name] = {"score": round(scaled, 2), "max": weight,
                            "input": metric_key, "value": value, "status": "AVAILABLE"}
    normalized = earned / possible * 50 if possible else 0.0
    coverage = possible / sum(weights.values())
    return ScoreResult(round(normalized, 2), 50.0, round(coverage, 3), components,
                       "COMPLETE" if coverage >= 0.9 else "PARTIAL")


def score_valuation(current_multiple: float | None, peer_multiple: float | None) -> ScoreResult:
    """Relative valuation score out of 30; lower positive multiple vs peers scores better."""
    if current_multiple is None or peer_multiple is None or current_multiple <= 0 or peer_multiple <= 0:
        return ScoreResult(0, 30, 0, {"relative_multiple": {"score": None, "max": 30,
                           "status": "MISSING"}}, "INSUFFICIENT_DATA")
    relative = current_multiple / peer_multiple
    points = 30 if relative <= .70 else 26 if relative <= .85 else 22 if relative <= 1 else 16 if relative <= 1.15 else 9 if relative <= 1.35 else 3
    return ScoreResult(points, 30, 1.0, {"relative_multiple": {"score": points, "max": 30,
                       "relative": round(relative, 4), "status": "AVAILABLE"}}, "COMPLETE")


def combine_score(fundamental: ScoreResult, valuation: ScoreResult,
                  technical_score_100: float | None) -> ScoreResult:
    """Legacy-compatible 100-point total: fundamentals 50, valuation 30, technical 20."""
    tech = None if technical_score_100 is None else max(0.0, min(100.0, technical_score_100)) * .2
    components = {
        "fundamental": {"score": fundamental.score, "max": 50, "coverage": fundamental.coverage},
        "valuation": {"score": valuation.score, "max": 30, "coverage": valuation.coverage},
        "technical": {"score": tech, "max": 20,
                      "status": "MISSING" if tech is None else "AVAILABLE"},
    }
    available = fundamental.score + valuation.score + (tech or 0)
    coverage = (fundamental.coverage * 50 + valuation.coverage * 30 + (20 if tech is not None else 0)) / 100
    return ScoreResult(round(available, 2), 100, round(coverage, 3), components,
                       "COMPLETE" if coverage >= .9 else "PARTIAL")

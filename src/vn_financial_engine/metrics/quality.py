"""Established financial-quality metrics. Inputs use consistent currency units."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def growth(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return current / previous - 1.0


def dupont_roe(net_income: float | None, revenue: float | None,
               average_assets: float | None, average_equity: float | None) -> dict[str, float | None]:
    """Three-step DuPont: net margin × asset turnover × equity multiplier."""
    margin = ratio(net_income, revenue)
    turnover = ratio(revenue, average_assets)
    multiplier = ratio(average_assets, average_equity)
    calculated = None if None in (margin, turnover, multiplier) else margin * turnover * multiplier
    return {"net_margin": margin, "asset_turnover": turnover,
            "equity_multiplier": multiplier, "dupont_roe": calculated}


def piotroski_f_score(current: Mapping[str, float | None],
                      prior: Mapping[str, float | None]) -> dict:
    """Nine-point Piotroski F-score for non-financial companies only.

    Required keys: roa, cfo, total_assets, long_term_debt, current_assets,
    current_liabilities, shares, gross_margin, asset_turnover.
    Missing/undefined tests are not silently scored as zero.
    """
    tests = {}
    def put(name: str, condition: bool | None):
        tests[name] = condition

    roa, proa = current.get("roa"), prior.get("roa")
    cfo, assets = current.get("cfo"), current.get("total_assets")
    put("positive_roa", roa > 0 if roa is not None else None)
    put("positive_cfo", cfo > 0 if cfo is not None else None)
    put("improving_roa", roa > proa if roa is not None and proa is not None else None)
    put("cashflow_exceeds_net_income",
        cfo > current["net_income"] if cfo is not None and current.get("net_income") is not None else None)

    for key, label, lower_is_better in (
        ("long_term_debt", "lower_leverage", True),
        ("current_ratio", "improving_liquidity", False),
        ("shares", "no_dilution", True),
        ("gross_margin", "improving_gross_margin", False),
        ("asset_turnover", "improving_asset_turnover", False),
    ):
        cur = current.get(key)
        old = prior.get(key)
        if key == "current_ratio":
            cur = ratio(current.get("current_assets"), current.get("current_liabilities"))
            old = ratio(prior.get("current_assets"), prior.get("current_liabilities"))
        if cur is None or old is None:
            put(label, None)
        else:
            put(label, cur < old if lower_is_better else cur >= old)

    known = [v for v in tests.values() if v is not None]
    score = sum(v is True for v in known)
    return {"score": score, "max_score": 9, "available_tests": len(known),
            "coverage": len(known) / 9, "tests": tests,
            "status": "COMPLETE" if len(known) == 9 else "PARTIAL"}


def non_financial_leverage(total_liabilities: float | None,
                           total_equity: float | None) -> float | None:
    return ratio(total_liabilities, total_equity)

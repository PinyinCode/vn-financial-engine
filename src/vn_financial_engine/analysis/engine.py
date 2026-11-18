"""End-to-end deterministic analysis orchestration for one issuer."""

from __future__ import annotations

from dataclasses import asdict

from vn_financial_engine.normalization.legacy import normalize_legacy_snapshot
from vn_financial_engine.scoring.scorecard import (
    combine_score, score_fundamentals, score_valuation,
)
from vn_financial_engine.valuation.engine import value_company
from vn_financial_engine.valuation.models import ValuationInput


def analyze_company(symbol: str, sector: str, legacy_stock: dict,
                    financial_metrics: dict, peer_multiples: dict,
                    technical: dict | None = None,
                    valuation_assumptions: dict | None = None) -> dict:
    """Build transparent scores and valuation from verified upstream inputs.

    Legacy market price/EPS/BVPS are converted from thousand VND to VND for
    per-share valuation. Ratios must already be decimals. FCFF, EBITDA and
    net debt must be VND totals; diluted_shares is a share count.
    """
    technical = technical or {}
    assumptions = valuation_assumptions or {}
    legacy = normalize_legacy_snapshot(legacy_stock, financial_metrics)
    metrics = {**financial_metrics}
    metrics.setdefault("roe", legacy.get("roe"))
    metrics.setdefault("profit_growth_yoy", legacy.get("profit_growth_yoy"))
    metrics.setdefault("debt_to_equity", legacy.get("debt_to_equity"))

    fund = score_fundamentals(metrics, sector)
    price = legacy.get("price_thousand_vnd")
    peer_payload = peer_multiples or {}
    peer_data = peer_payload.get("multiples", peer_payload)

    def peer_value(key):
        value = peer_data.get(key)
        return value.get("median") if isinstance(value, dict) else value
    primary = str(assumptions.get("primary_multiple", "PB" if sector.upper() in
                    {"BANK", "SECURITIES"} else "PE")).lower()
    current_multiple = legacy.get(primary)
    if primary == "ps":
        current_multiple = assumptions.get("current_ps")
        if current_multiple is None:
            revenue_per_share = assumptions.get("revenue_per_share_vnd")
            current_multiple = (
                price * 1000 / revenue_per_share
                if price is not None and revenue_per_share not in (None, 0)
                else None
            )
    elif primary == "ev_ebitda":
        current_multiple = assumptions.get("current_ev_ebitda")
        ebitda = assumptions.get("ebitda_vnd")
        net_debt = assumptions.get("net_debt_vnd")
        shares = assumptions.get("diluted_shares")
        if (current_multiple is None and price is not None and ebitda not in (None, 0)
                and net_debt is not None and shares is not None and shares > 0):
            market_cap = price * 1000 * shares
            current_multiple = (market_cap + net_debt) / ebitda
    else:
        current_multiple = assumptions.get("current_multiple", current_multiple)
    peer_multiple = peer_value(primary)
    valuation_score = score_valuation(current_multiple, peer_multiple)
    technical_score = technical.get("technical_score")
    if technical.get("technical_coverage", 1) < 1:
        technical_score = None
    total = combine_score(fund, valuation_score, technical_score)

    price = legacy.get("price_thousand_vnd")
    eps = legacy.get("eps_ttm_thousand_vnd")
    bvps = legacy.get("bvps_thousand_vnd")
    valuation_input = ValuationInput(
        price=(price * 1000 if price is not None else 0),
        eps_ttm=(eps * 1000 if eps is not None else None),
        bvps=(bvps * 1000 if bvps is not None else None),
        roe=metrics.get("roe"),
        revenue_per_share=assumptions.get("revenue_per_share_vnd"),
        ebitda=assumptions.get("ebitda_vnd"),
        diluted_shares=assumptions.get("diluted_shares"),
        net_debt=assumptions.get("net_debt_vnd"),
        fcff=assumptions.get("fcff_vnd"),
        dividend_per_share=assumptions.get("dividend_per_share_vnd"),
        growth_rate=assumptions.get("growth_rate"),
        terminal_growth=assumptions.get("terminal_growth"),
        cost_of_equity=assumptions.get("cost_of_equity"),
        wacc=assumptions.get("wacc"),
        forecast_years=int(assumptions.get("forecast_years", 5)),
        peer_pe=peer_value("pe"),
        peer_pb=peer_value("pb"),
        peer_ps=peer_value("ps"),
        peer_ev_ebitda=peer_value("ev_ebitda"),
        sector=sector,
        is_bank=sector.upper() == "BANK",
    )
    valuation = value_company(
        valuation_input,
        margin_of_safety=float(assumptions.get("margin_of_safety", .25)),
    )
    return {
        "symbol": symbol.upper(),
        "sector": sector.upper(),
        "unit_profile": "VND_PER_SHARE; VND_TOTALS; DECIMAL_RATIOS",
        "metrics": metrics,
        "technical": technical,
        "peer_comparison": peer_payload,
        "scores": asdict(total),
        "fundamental_score": asdict(fund),
        "valuation_score": asdict(valuation_score),
        "valuation": asdict(valuation),
        "data_quality": {
            "legacy_snapshot": legacy,
            "financial_metric_count": len(metrics),
            "valuation_method_count": len(valuation.methods),
            "valuation_status": valuation.status,
        },
    }

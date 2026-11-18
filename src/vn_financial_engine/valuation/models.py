"""Valuation contracts. Currency units must be consistent within each method."""

from dataclasses import dataclass, field

VALUATION_FORMULA_VERSION = "sector-valuation-v2.1-2026-11-18"


@dataclass(frozen=True)
class ValuationInput:
    price: float
    eps_ttm: float | None = None
    bvps: float | None = None
    roe: float | None = None
    revenue_per_share: float | None = None
    ebitda: float | None = None
    diluted_shares: float | None = None
    net_debt: float | None = None
    fcff: float | None = None
    dividend_per_share: float | None = None
    growth_rate: float | None = None
    terminal_growth: float | None = None
    cost_of_equity: float | None = None
    wacc: float | None = None
    forecast_years: int = 5
    peer_pe: float | None = None
    peer_pb: float | None = None
    peer_ps: float | None = None
    peer_ev_ebitda: float | None = None
    sector: str = "OTHER"
    is_bank: bool = False
    allowed_methods: tuple[str, ...] | None = None


@dataclass
class ValuationResult:
    methods: dict[str, float] = field(default_factory=dict)
    method_weights: dict[str, float] = field(default_factory=dict)
    fair_value: float | None = None
    fair_value_low: float | None = None
    fair_value_high: float | None = None
    buy_below: float | None = None
    margin_of_safety: float | None = None
    upside_to_fair_value: float | None = None
    status: str = "INSUFFICIENT_DATA"
    excluded_methods: dict[str, str] = field(default_factory=dict)
    assumptions: dict[str, float | int | str] = field(default_factory=dict)
    formula_version: str = VALUATION_FORMULA_VERSION

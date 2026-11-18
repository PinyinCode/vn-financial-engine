"""Typed-by-convention valuation inputs and outputs; currency per share unless stated."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValuationInput:
    price: float
    eps_ttm: float | None = None
    bvps: float | None = None
    revenue_per_share: float | None = None
    ebitda_per_share: float | None = None
    free_cash_flow_per_share: float | None = None
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
    target_payout: float | None = None
    sector: str = "OTHER"
    is_bank: bool = False


@dataclass
class ValuationResult:
    methods: dict[str, float] = field(default_factory=dict)
    method_weights: dict[str, float] = field(default_factory=dict)
    fair_value: float | None = None
    fair_value_low: float | None = None
    fair_value_high: float | None = None
    margin_of_safety: float | None = None
    upside_to_fair_value: float | None = None
    status: str = "INSUFFICIENT_DATA"
    excluded_methods: dict[str, str] = field(default_factory=dict)
    assumptions: dict[str, float | int | str] = field(default_factory=dict)

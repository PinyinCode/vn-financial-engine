"""Relative valuation methods using peer multiples, not arbitrary universal multiples."""

from __future__ import annotations

from .models import ValuationInput


def calculate_multiples(data: ValuationInput) -> tuple[dict[str, float], dict[str, str]]:
    values: dict[str, float] = {}
    excluded: dict[str, str] = {}

    methods = (
        ("PE", data.eps_ttm, data.peer_pe),
        ("PB", data.bvps, data.peer_pb),
        ("PS", data.revenue_per_share, data.peer_ps),
        ("EV_EBITDA_PROXY", data.ebitda_per_share, data.peer_ev_ebitda),
    )
    for name, per_share_metric, peer_multiple in methods:
        if per_share_metric is None or per_share_metric <= 0:
            excluded[name] = "Thiếu hoặc chỉ tiêu trên mỗi cổ phiếu không dương"
        elif peer_multiple is None or peer_multiple <= 0:
            excluded[name] = "Thiếu trung vị peer hợp lệ"
        else:
            values[name] = per_share_metric * peer_multiple

    # Graham's simplified defensive valuation formula: sqrt(22.5 × EPS × BVPS).
    # Used as a cross-check only, not for banks or loss-making issuers.
    if not data.is_bank and data.eps_ttm and data.eps_ttm > 0 and data.bvps and data.bvps > 0:
        values["GRAHAM"] = (22.5 * data.eps_ttm * data.bvps) ** 0.5
    else:
        excluded["GRAHAM"] = "Không phù hợp ngành tài chính hoặc thiếu EPS/BVPS dương"
    return values, excluded

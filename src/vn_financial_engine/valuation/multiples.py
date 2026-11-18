"""Relative valuation with sector eligibility checks and EV-to-equity bridge."""

from __future__ import annotations

from .models import ValuationInput


def calculate_multiples(
    data: ValuationInput, allowed_methods: set[str] | None = None
) -> tuple[dict[str, float], dict[str, str]]:
    values: dict[str, float] = {}
    excluded: dict[str, str] = {}
    allowed = allowed_methods or {"PE", "PB", "PS", "EV_EBITDA", "GRAHAM"}

    for name, metric, multiple in (
        ("PE", data.eps_ttm, data.peer_pe),
        ("PB", data.bvps, data.peer_pb),
        ("PS", data.revenue_per_share, data.peer_ps),
    ):
        if name not in allowed:
            excluded[name] = "Phương pháp không nằm trong cấu hình ngành"
        elif metric is None or metric <= 0:
            excluded[name] = "Thiếu hoặc chỉ tiêu trên mỗi cổ phiếu không dương"
        elif multiple is None or multiple <= 0:
            excluded[name] = "Thiếu trung vị peer hợp lệ"
        else:
            values[name] = metric * multiple

    if "EV_EBITDA" not in allowed:
        excluded["EV_EBITDA"] = "EV/EBITDA không phù hợp cấu hình ngành"
    elif (data.ebitda is not None and data.ebitda > 0
          and data.peer_ev_ebitda is not None and data.peer_ev_ebitda > 0
          and data.net_debt is not None and data.diluted_shares is not None
          and data.diluted_shares > 0):
        enterprise_value = data.ebitda * data.peer_ev_ebitda
        equity_value = enterprise_value - data.net_debt
        per_share = equity_value / data.diluted_shares
        if per_share > 0:
            values["EV_EBITDA"] = per_share
        else:
            excluded["EV_EBITDA"] = "Giá trị vốn chủ sau khi trừ nợ ròng không dương"
    else:
        excluded["EV_EBITDA"] = (
            "Thiếu EBITDA, peer EV/EBITDA, nợ ròng hoặc cổ phiếu pha loãng"
        )

    if "GRAHAM" not in allowed:
        excluded["GRAHAM"] = "Graham không nằm trong cấu hình ngành"
    elif (not data.is_bank and data.eps_ttm is not None and data.eps_ttm > 0
          and data.bvps is not None and data.bvps > 0):
        values["GRAHAM"] = (22.5 * data.eps_ttm * data.bvps) ** 0.5
    else:
        excluded["GRAHAM"] = "Không phù hợp ngân hàng hoặc thiếu EPS/BVPS dương"
    return values, excluded

"""Relative valuation using peer multiples and the EV-to-equity bridge."""

from __future__ import annotations

from .models import ValuationInput


def calculate_multiples(data: ValuationInput) -> tuple[dict[str, float], dict[str, str]]:
    values: dict[str, float] = {}
    excluded: dict[str, str] = {}
    for name, metric, multiple in (
        ("PE", data.eps_ttm, data.peer_pe),
        ("PB", data.bvps, data.peer_pb),
        ("PS", data.revenue_per_share, data.peer_ps),
    ):
        if metric is None or metric <= 0:
            excluded[name] = "Thiếu hoặc chỉ tiêu trên mỗi cổ phiếu không dương"
        elif multiple is None or multiple <= 0:
            excluded[name] = "Thiếu trung vị peer hợp lệ"
        else:
            values[name] = metric * multiple

    if (data.ebitda is not None and data.ebitda > 0
            and data.peer_ev_ebitda is not None and data.peer_ev_ebitda > 0
            and data.net_debt is not None and data.diluted_shares is not None
            and data.diluted_shares > 0):
        equity_value = data.ebitda * data.peer_ev_ebitda - data.net_debt
        per_share = equity_value / data.diluted_shares
        if per_share > 0:
            values["EV_EBITDA"] = per_share
        else:
            excluded["EV_EBITDA"] = "Giá trị vốn chủ sau khi trừ nợ ròng không dương"
    else:
        excluded["EV_EBITDA"] = "Thiếu EBITDA, peer EV/EBITDA, nợ ròng hoặc cổ phiếu pha loãng"

    # Graham's simplified defensive formula is only a cross-check for non-financial issuers.
    if not data.is_bank and data.eps_ttm and data.eps_ttm > 0 and data.bvps and data.bvps > 0:
        values["GRAHAM"] = (22.5 * data.eps_ttm * data.bvps) ** 0.5
    else:
        excluded["GRAHAM"] = "Không phù hợp ngân hàng hoặc thiếu EPS/BVPS dương"
    return values, excluded

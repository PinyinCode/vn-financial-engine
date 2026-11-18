"""Peer-group multiple statistics with minimum sample and outlier controls."""

from __future__ import annotations

import math
from statistics import median


MULTIPLE_KEYS = ("pe", "pb", "ps", "ev_ebitda")


def _valid_multiple(value) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def _iqr_filter(values: list[tuple[str, float]]) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Tukey 1.5×IQR fences; only used with at least five peer observations."""
    ordered = sorted(value for _, value in values)
    q1 = ordered[len(ordered) // 4]
    q3 = ordered[(3 * len(ordered)) // 4]
    spread = q3 - q1
    low, high = q1 - 1.5 * spread, q3 + 1.5 * spread
    kept = [(symbol, value) for symbol, value in values if low <= value <= high]
    removed = [(symbol, value) for symbol, value in values if not low <= value <= high]
    return kept, removed


def build_peer_multiples(
    peers: list[dict],
    *,
    subject_symbol: str,
    sector: str,
    peer_group: str | None = None,
    min_peers: int = 3,
) -> dict:
    """Return peer medians only when the same-sector peer sample is sufficient.

    Each peer record contains symbol, sector, optional peer_group and multiples.
    The subject issuer is always removed. Outlier filtering is only activated
    for samples of at least five valid observations.
    """
    if min_peers < 3:
        raise ValueError("min_peers không được nhỏ hơn 3")
    subject = str(subject_symbol).upper()
    sector = str(sector).upper()
    eligible = []
    excluded_companies = []
    for peer in peers or []:
        symbol = str(peer.get("symbol", "")).upper()
        if not symbol or symbol == subject:
            excluded_companies.append({"symbol": symbol, "reason": "SELF_OR_MISSING_SYMBOL"})
            continue
        if str(peer.get("sector", "")).upper() != sector:
            excluded_companies.append({"symbol": symbol, "reason": "SECTOR_MISMATCH"})
            continue
        if peer_group and peer.get("peer_group") != peer_group:
            excluded_companies.append({"symbol": symbol, "reason": "PEER_GROUP_MISMATCH"})
            continue
        eligible.append(peer)

    output = {"sector": sector, "peer_group": peer_group, "subject_symbol": subject,
              "min_peers": min_peers, "multiples": {}, "eligible_symbols": [
                  str(p["symbol"]).upper() for p in eligible
              ], "excluded_companies": excluded_companies}

    for key in MULTIPLE_KEYS:
        values = [(str(p["symbol"]).upper(), float(p[key]))
                  for p in eligible if _valid_multiple(p.get(key))]
        removed = []
        if len(values) >= 5:
            values, removed = _iqr_filter(values)
        if len(values) < min_peers:
            output["multiples"][key] = {
                "median": None, "peer_count": len(values),
                "status": "INSUFFICIENT_PEERS",
                "symbols": [symbol for symbol, _ in values],
                "outliers_excluded": [symbol for symbol, _ in removed],
            }
            continue
        output["multiples"][key] = {
            "median": median(value for _, value in values),
            "peer_count": len(values), "status": "CALCULATED",
            "symbols": [symbol for symbol, _ in values],
            "outliers_excluded": [symbol for symbol, _ in removed],
            "statistic": "MEDIAN",
        }
    return output

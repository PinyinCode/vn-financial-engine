"""Unit-aware bridge from the old price_api.py MongoDB document shape."""

from __future__ import annotations


def _number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _percent_to_decimal(value):
    number = _number(value)
    return None if number is None else number / 100.0


def normalize_legacy_snapshot(stock: dict, bctc_metrics: dict | None = None) -> dict:
    """Map legacy stock snapshot to engine units without inventing missing values.

    Legacy conventions observed in price_api.py:
    - close/close_price and EPS are stored in thousand VND.
    - ROE/ROA/dividend_yield/profit_growth_yoy are percentages.
    - PE/PB/debt_to_equity are multiples.
    """
    bctc_metrics = bctc_metrics or {}
    price = _number(stock.get("close", stock.get("close_price")))
    eps = _number(stock.get("eps"))
    pb = _number(stock.get("pb"))
    bvps = price / pb if price is not None and price > 0 and pb and pb > 0 else None
    return {
        "symbol": str(stock.get("symbol", "")).upper().strip(),
        "price_thousand_vnd": price,
        "eps_ttm_thousand_vnd": eps,
        "bvps_thousand_vnd": bvps,
        "pe": _number(stock.get("pe")),
        "pb": pb,
        "roe": _percent_to_decimal(stock.get("roe")),
        "roa": _percent_to_decimal(stock.get("roa")),
        "dividend_yield": _percent_to_decimal(stock.get("dividend_yield")),
        "profit_growth_yoy": _percent_to_decimal(
            stock.get("profit_growth_yoy", bctc_metrics.get("profit_growth_yoy"))
        ),
        "debt_to_equity": _number(
            stock.get("debt_to_equity", bctc_metrics.get("debt_to_equity"))
        ),
        "net_profit_ttm_billion_vnd": _number(
            stock.get("net_profit_ttm", bctc_metrics.get("net_profit_ttm"))
        ),
        "cfo_ttm_billion_vnd": _number(
            stock.get("cfo_latest", bctc_metrics.get("cfo_latest"))
        ),
        "source": "LEGACY_MONGO",
        "unit_profile": "LEGACY_PRICE_API_V1",
    }

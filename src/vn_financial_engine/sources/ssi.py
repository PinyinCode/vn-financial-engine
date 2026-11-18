"""SSI/Vnstock market-price adapter, based on the legacy price_api.py.

Stored prices are in thousand VND and volume is normalized using the legacy
VOLUME_MULTIPLIER convention. The caller owns persistence and freshness checks.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import re
import time

import pandas as pd

logger = logging.getLogger(__name__)


def _market():
    try:
        from vnstock import Market
    except ImportError as exc:
        raise RuntimeError('Cần cài extra market-data: pip install .[market-data]') from exc
    return Market()


class SSIPriceAdapter:
    def __init__(self, volume_multiplier: int = 10):
        self.volume_multiplier = volume_multiplier

    @staticmethod
    def _vn_now() -> datetime:
        return datetime.now(timezone.utc) + timedelta(hours=7)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        value = str(symbol or "").upper().strip()
        if not re.fullmatch(r"[A-Z0-9]{2,10}", value):
            raise ValueError(f"Mã chứng khoán không hợp lệ: {symbol!r}")
        return value

    def fetch_history(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
        symbol = self._normalize_symbol(symbol)
        try:
            df = _market().equity(symbol).ohlcv(
                start=start_date, end=end_date, interval="1D", source="ssi"
            )
            if df is None or df.empty:
                return None
            df = df.copy()
            df.columns = [str(c).lower().strip() for c in df.columns]
            if "time" not in df.columns:
                alias = next((c for c in ("date", "datetime", "trading_date", "tradingdate")
                              if c in df.columns), None)
                if alias:
                    df = df.rename(columns={alias: "time"})
                elif isinstance(df.index, pd.DatetimeIndex) or df.index.name:
                    df = df.reset_index()
                    df.columns = [str(c).lower().strip() for c in df.columns]
                    if "time" not in df.columns:
                        alias = next((c for c in ("index", "date", "datetime",
                                      "trading_date", "tradingdate") if c in df.columns), None)
                        if alias:
                            df = df.rename(columns={alias: "time"})
            required = {"time", "open", "high", "low", "close", "volume"}
            if required.difference(df.columns):
                logger.error("%s: thiếu cột OHLCV %s", symbol, sorted(required.difference(df.columns)))
                return None
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            for col in ("open", "high", "low", "close", "volume"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=list(required))
            df = df[(df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0)
                    & (df["close"] > 0) & (df["volume"] >= 0)]
            if not df.empty and float(df["close"].median()) >= 1000:
                df[["open", "high", "low", "close"]] /= 1000.0
            mask = (df["volume"] > 0) & (df["volume"] < 100000)
            df.loc[mask, "volume"] *= self.volume_multiplier
            df = df[(df["high"] >= df[["open", "low", "close"]].max(axis=1))
                    & (df["low"] <= df[["open", "high", "close"]].min(axis=1))]
            df = df.drop_duplicates(subset=["time"], keep="last").sort_values("time")
            return df.reset_index(drop=True) if not df.empty else None
        except Exception:
            logger.exception("SSI history fetch failed for %s", symbol)
            return None

    def fetch_snapshot(self, symbol: str, retries: int = 3) -> dict | None:
        """Aggregate current VN trading-day 1-minute candles; never relabel stale bars."""
        symbol = self._normalize_symbol(symbol)
        today = self._vn_now().strftime("%Y-%m-%d")
        start = (self._vn_now() - timedelta(days=7)).strftime("%Y-%m-%d")
        last_error = None
        for attempt in range(retries):
            try:
                frame = Market().equity(symbol).ohlcv(
                    start=start, end=today, interval="1m", source="ssi"
                )
                if frame is None or frame.empty:
                    return None
                frame = frame.copy()
                frame.columns = [str(c).lower().strip() for c in frame.columns]
                if "time" not in frame.columns:
                    frame = frame.reset_index()
                    frame.columns = [str(c).lower().strip() for c in frame.columns]
                    if "time" not in frame.columns:
                        frame = frame.rename(columns={frame.columns[0]: "time"})
                if "time" not in frame.columns:
                    return None
                frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
                frame = frame.dropna(subset=["time"])
                frame = frame[frame["time"].dt.strftime("%Y-%m-%d") == today].sort_values("time")
                if frame.empty:
                    logger.warning("[FETCH STALE] %s: SSI không có nến 1m ngày %s", symbol, today)
                    return None
                for col in ("open", "high", "low", "close", "volume"):
                    if col not in frame.columns:
                        return None
                    frame[col] = pd.to_numeric(frame[col], errors="coerce")
                frame = frame.dropna(subset=["open", "high", "low", "close"])
                frame = frame[(frame["open"] > 0) & (frame["high"] > 0)
                              & (frame["low"] > 0) & (frame["close"] > 0)]
                if frame.empty:
                    return None
                first, last = frame.iloc[0], frame.iloc[-1]
                result = {
                    "close": float(last["close"]), "open": float(first["open"]),
                    "high": float(frame["high"].max()), "low": float(frame["low"].min()),
                    "volume": int(frame["volume"].fillna(0).clip(lower=0).sum()),
                    "source_time": last["time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "source_date": today, "source": "SSI/Vnstock",
                }
                if result["close"] >= 1000:
                    for key in ("close", "open", "high", "low"):
                        result[key] /= 1000.0
                if 0 < result["volume"] < 100000:
                    result["volume"] *= self.volume_multiplier
                return result
            except Exception as exc:
                last_error = exc
                text = str(exc).lower()
                limited = "429" in text or "ratelimit" in type(exc).__name__.lower()
                if not limited or attempt + 1 >= retries:
                    break
                time.sleep(min(8, 1 + attempt * 2))
        logger.error("SSI snapshot failed for %s: %s", symbol, last_error)
        return None

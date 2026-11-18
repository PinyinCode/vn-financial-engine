"""Technical-analysis module ported from the legacy ptkt.py.

The original indicator definitions and point allocation are preserved as the
first compatibility baseline. Review and version any later formula changes.
"""
import json
import os
import numpy as np
import pandas as pd


class ProfessionalTechnicalAnalyzer:
    """
    Bộ phân tích kỹ thuật theo thang 100 điểm, đồng bộ với technical_score 20 điểm
    trong price_api.py. Điểm gồm Trend 30, Momentum 25, Volume 20, Structure 25.
    Không dùng điểm nền 50; dữ liệu thiếu không được tự động cộng điểm.
    """

    def __init__(self, history_data_or_path):
        self.df = pd.DataFrame()
        self.data_warnings = []
        self._load_data(history_data_or_path)
        self._validate_and_prepare()

    def _load_data(self, source):
        raw_data = []
        if isinstance(source, str):
            if os.path.exists(source):
                try:
                    with open(source, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    if isinstance(payload, dict):
                        raw_data = payload.get("history_d1")
                        if raw_data is None:
                            raw_data = payload.get("data", [])
                    elif isinstance(payload, list):
                        raw_data = payload
                except Exception as exc:
                    self.data_warnings.append(f"Không đọc được file lịch sử: {exc}")
        elif isinstance(source, pd.DataFrame):
            self.df = source.copy()
        elif isinstance(source, list):
            raw_data = source

        if self.df.empty and isinstance(raw_data, list) and raw_data:
            self.df = pd.DataFrame(raw_data)

    @staticmethod
    def _normalize_columns(df):
        aliases = {
            "time": ("time", "date", "trading_date", "datetime", "timestamp"),
            "open": ("open", "o"),
            "high": ("high", "h"),
            "low": ("low", "l"),
            "close": ("close", "c", "adj_close", "adjclose"),
            "volume": ("volume", "vol", "total_volume"),
        }
        lower_map = {str(col).strip().lower(): col for col in df.columns}
        rename = {}
        for canonical, candidates in aliases.items():
            if canonical in df.columns:
                continue
            for candidate in candidates:
                if candidate in lower_map:
                    rename[lower_map[candidate]] = canonical
                    break
        return df.rename(columns=rename)

    def _validate_and_prepare(self):
        if self.df.empty:
            self.data_warnings.append("Không có dữ liệu lịch sử")
            return

        self.df = self._normalize_columns(self.df)
        required = ["high", "low", "close", "volume"]
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            self.data_warnings.append("Thiếu cột bắt buộc: " + ", ".join(missing))
            self.df = pd.DataFrame()
            return

        for col in ["open", "high", "low", "close", "volume"]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        before = len(self.df)
        self.df = self.df.dropna(subset=required).copy()
        self.df = self.df[
            (self.df["high"] > 0)
            & (self.df["low"] > 0)
            & (self.df["close"] > 0)
            & (self.df["volume"] >= 0)
            & (self.df["high"] >= self.df["low"])
            & (self.df["close"] <= self.df["high"])
            & (self.df["close"] >= self.df["low"])
        ].copy()

        if "open" in self.df.columns:
            self.df = self.df[
                self.df["open"].isna()
                | (
                    (self.df["open"] > 0)
                    & (self.df["open"] <= self.df["high"])
                    & (self.df["open"] >= self.df["low"])
                )
            ].copy()

        removed = before - len(self.df)
        if removed:
            self.data_warnings.append(f"Đã loại {removed} dòng OHLCV lỗi hoặc thiếu")

        if "time" in self.df.columns:
            parsed = pd.to_datetime(self.df["time"], errors="coerce", utc=True)
            if parsed.notna().any():
                self.df["_parsed_time"] = parsed
                self.df = self.df.sort_values("_parsed_time")
                duplicate_count = int(self.df.duplicated(subset=["_parsed_time"], keep="last").sum())
                if duplicate_count:
                    self.data_warnings.append(f"Loại {duplicate_count} nến trùng thời gian")
                    self.df = self.df.drop_duplicates(subset=["_parsed_time"], keep="last")
                self.df["time"] = self.df["_parsed_time"]
                self.df = self.df.drop(columns=["_parsed_time"])
            else:
                self.data_warnings.append("Không đọc được định dạng thời gian; giữ thứ tự dữ liệu nguồn")

        self.df = self.df.reset_index(drop=True)
        if self.df.empty:
            return

        close = self.df["close"]
        self.df["ema20"] = close.ewm(span=20, adjust=False, min_periods=20).mean()
        self.df["ema50"] = close.ewm(span=50, adjust=False, min_periods=50).mean()
        self.df["ema200"] = close.ewm(span=200, adjust=False, min_periods=200).mean()
        self.df["sma20"] = close.rolling(20, min_periods=20).mean()
        self.df["sma50"] = close.rolling(50, min_periods=50).mean()
        self.df["vol_ma20"] = self.df["volume"].rolling(20, min_periods=20).mean()

        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        rs = gain / loss.replace(0, np.nan)
        self.df["rsi14"] = 100 - (100 / (1 + rs))
        self.df.loc[(loss == 0) & (gain > 0), "rsi14"] = 100
        self.df.loc[(loss == 0) & (gain == 0), "rsi14"] = 50

        ema12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
        ema26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
        self.df["macd"] = ema12 - ema26
        self.df["macd_signal"] = self.df["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
        self.df["macd_hist"] = self.df["macd"] - self.df["macd_signal"]
        self.df["roc20"] = close.pct_change(20) * 100

        direction = np.sign(close.diff()).fillna(0)
        self.df["obv"] = (direction * self.df["volume"]).cumsum()
        self.df["obv_ma10"] = self.df["obv"].rolling(10, min_periods=10).mean()

    @staticmethod
    def _valid(value):
        return value is not None and pd.notna(value) and np.isfinite(float(value))

    def _detect_darvas_box(self, window=40):
        if len(self.df) < window:
            return False
        recent = self.df.tail(window)
        box_top = float(recent["high"].iloc[:-5].max())
        avg_vol = recent["vol_ma20"].iloc[-1]
        if not self._valid(avg_vol) or avg_vol <= 0:
            return False
        return bool(
            recent["close"].iloc[-1] > box_top
            and recent["volume"].iloc[-1] >= avg_vol * 1.3
        )

    def _detect_double_bottom(self, lookback=70):
        if len(self.df) < lookback:
            return False
        recent = self.df.tail(lookback).reset_index(drop=True)
        lows = recent["low"].to_numpy()
        troughs = []
        for i in range(2, len(lows) - 2):
            if lows[i] <= lows[i - 1] and lows[i] <= lows[i + 1] and lows[i] <= lows[i - 2] and lows[i] <= lows[i + 2]:
                troughs.append((i, float(lows[i])))
        if len(troughs) < 2:
            return False
        first, second = troughs[-2], troughs[-1]
        if not 8 <= second[0] - first[0] <= 50:
            return False
        if first[1] <= 0 or abs(first[1] - second[1]) / first[1] > 0.04:
            return False
        neckline = float(recent["high"].iloc[first[0]:second[0] + 1].max())
        return bool(recent["close"].iloc[-1] > neckline)

    def _detect_spring_washout(self, lookback=45):
        if len(self.df) < lookback:
            return False
        recent = self.df.tail(lookback)
        support = float(recent["low"].iloc[:-5].min())
        avg_vol = float(recent["volume"].iloc[:-5].mean())
        if support <= 0 or avg_vol <= 0:
            return False
        for i in range(max(0, len(recent) - 3), len(recent)):
            row = recent.iloc[i]
            candle_range = float(row["high"] - row["low"])
            if candle_range <= 0:
                continue
            close_position = float((row["close"] - row["low"]) / candle_range)
            if row["low"] < support * 0.995 and close_position >= 0.6 and row["volume"] >= avg_vol * 1.2:
                return True
        return False

    def _detect_accumulation(self, lookback=45):
        if len(self.df) < lookback:
            return False
        recent = self.df.tail(lookback)
        mean_close = float(recent["close"].mean())
        if mean_close <= 0:
            return False
        range_pct = float((recent["high"].max() - recent["low"].min()) / mean_close)
        volumes = recent["volume"].to_numpy()
        mid = len(volumes) // 2
        first_avg = float(np.mean(volumes[:mid]))
        second_avg = float(np.mean(volumes[mid:]))
        return bool(range_pct <= 0.15 and first_avg > 0 and second_avg < first_avg * 0.85)

    def _evaluate_volume_behavior(self):
        if len(self.df) < 20:
            return "Chưa đủ 20 phiên để đánh giá khối lượng"
        avg_vol = self.df["vol_ma20"].iloc[-1]
        latest_vol = self.df["volume"].iloc[-1]
        if not self._valid(avg_vol) or avg_vol <= 0:
            return "Khối lượng bình quân không hợp lệ"
        ratio = float(latest_vol / avg_vol)
        if ratio >= 1.5:
            return f"Khối lượng tăng mạnh ({ratio:.2f}x MA20)"
        if ratio >= 1.1:
            return f"Khối lượng tăng ({ratio:.2f}x MA20)"
        if ratio <= 0.7:
            return f"Khối lượng thấp ({ratio:.2f}x MA20)"
        return f"Khối lượng bình thường ({ratio:.2f}x MA20)"

    def _score_trend(self, latest):
        score, reasons = 0, []
        close = float(latest["close"])
        ema20, ema50, ema200 = latest["ema20"], latest["ema50"], latest["ema200"]
        if self._valid(ema20):
            if close > ema20:
                score += 8
                reasons.append("Giá trên EMA20 (+8)")
            else:
                reasons.append("Giá dưới EMA20")
        if self._valid(ema20) and self._valid(ema50):
            if ema20 > ema50:
                score += 8
                reasons.append("EMA20 trên EMA50 (+8)")
            else:
                reasons.append("EMA20 chưa vượt EMA50")
        if len(self.df) >= 60 and self._valid(self.df["ema50"].iloc[-11]):
            slope = float(ema50 - self.df["ema50"].iloc[-11])
            if slope > 0:
                score += 6
                reasons.append("EMA50 dốc lên (+6)")
            else:
                reasons.append("EMA50 đi ngang/giảm")
        if self._valid(ema200):
            if close > ema200:
                score += 8
                reasons.append("Giá trên EMA200 (+8)")
            else:
                reasons.append("Giá dưới EMA200")
        return min(score, 30), reasons

    def _score_momentum(self, latest):
        score, reasons = 0, []
        rsi = latest["rsi14"]
        if self._valid(rsi):
            rsi = float(rsi)
            if 52 <= rsi <= 68:
                score += 10
                reasons.append(f"RSI {rsi:.1f}: động lượng tích cực (+10)")
            elif 45 <= rsi < 52:
                score += 6
                reasons.append(f"RSI {rsi:.1f}: động lượng hồi phục (+6)")
            elif 68 < rsi <= 75:
                score += 6
                reasons.append(f"RSI {rsi:.1f}: mạnh nhưng nóng (+6)")
            elif rsi > 75:
                score += 2
                reasons.append(f"RSI {rsi:.1f}: quá mua, hạn chế điểm (+2)")
            else:
                reasons.append(f"RSI {rsi:.1f}: động lượng yếu")
        hist = latest["macd_hist"]
        if self._valid(hist):
            if hist > 0:
                score += 8
                reasons.append("MACD histogram dương (+8)")
            else:
                reasons.append("MACD histogram âm")
        roc = latest["roc20"]
        if self._valid(roc):
            if roc >= 5:
                score += 7
                reasons.append(f"ROC20 {roc:.1f}% tích cực (+7)")
            elif roc > 0:
                score += 4
                reasons.append(f"ROC20 {roc:.1f}% dương (+4)")
            else:
                reasons.append(f"ROC20 {roc:.1f}% âm")
        return min(score, 25), reasons

    def _score_volume(self):
        score, reasons = 0, []
        if len(self.df) < 20:
            return score, ["Thiếu dữ liệu khối lượng 20 phiên"]
        recent = self.df.tail(20)
        avg = float(recent["vol_ma20"].iloc[-1])
        if not self._valid(avg) or avg <= 0:
            return score, ["Khối lượng bình quân không hợp lệ"]
        ratio = float(recent["volume"].iloc[-1] / avg)
        if 1.2 <= ratio <= 2.5:
            score += 8
            reasons.append(f"Volume {ratio:.2f}x MA20 (+8)")
        elif ratio > 2.5:
            score += 5
            reasons.append(f"Volume đột biến {ratio:.2f}x; giảm điểm do rủi ro phân phối (+5)")
        elif ratio >= 0.8:
            score += 5
            reasons.append(f"Volume duy trì {ratio:.2f}x MA20 (+5)")
        else:
            score += 2
            reasons.append(f"Volume thấp {ratio:.2f}x MA20 (+2)")

        changes = recent["close"].diff()
        up_volume = float(recent.loc[changes > 0, "volume"].sum())
        down_volume = float(recent.loc[changes < 0, "volume"].sum())
        total_directional = up_volume + down_volume
        if total_directional > 0:
            up_ratio = up_volume / total_directional
            if up_ratio >= 0.60:
                score += 7
                reasons.append("Khối lượng phiên tăng chiếm ưu thế (+7)")
            elif up_ratio >= 0.52:
                score += 4
                reasons.append("Khối lượng phiên tăng nhỉnh hơn (+4)")
            else:
                reasons.append("Khối lượng phiên giảm chiếm ưu thế")
        obv = self.df["obv"].iloc[-1]
        obv_ma = self.df["obv_ma10"].iloc[-1]
        if self._valid(obv) and self._valid(obv_ma):
            if obv > obv_ma:
                score += 5
                reasons.append("OBV trên trung bình 10 phiên (+5)")
            else:
                reasons.append("OBV chưa xác nhận dòng tiền")
        return min(score, 20), reasons

    def _score_structure(self, darvas, double_bottom, spring, accumulation):
        score, reasons = 0, []
        if len(self.df) >= 21:
            prior_resistance = float(self.df["high"].iloc[-21:-1].max())
            current_close = float(self.df["close"].iloc[-1])
            if current_close > prior_resistance:
                score += 12
                reasons.append("Đóng cửa vượt đỉnh 20 phiên (+12)")
            else:
                reasons.append("Chưa vượt đỉnh 20 phiên")
        if len(self.df) >= 40:
            recent = self.df.tail(40)
            first_half = recent.iloc[:20]
            second_half = recent.iloc[20:]
            higher_high = second_half["high"].max() > first_half["high"].max()
            higher_low = second_half["low"].min() > first_half["low"].min()
            if higher_high and higher_low:
                score += 8
                reasons.append("Cấu trúc đỉnh sau/đáy sau cao hơn (+8)")
            elif higher_low:
                score += 4
                reasons.append("Đáy sau cao hơn (+4)")
        if darvas:
            score += 5
            reasons.append("Darvas breakout được volume xác nhận (+5)")
        elif double_bottom:
            score += 5
            reasons.append("Mô hình hai đáy xác nhận neckline (+5)")
        elif spring:
            score += 4
            reasons.append("Spring/Washout có lực cầu xác nhận (+4)")
        elif accumulation:
            score += 3
            reasons.append("Nền tích lũy, volume co hẹp (+3)")
        return min(score, 25), reasons

    def analyze(self):
        empty_result = {
            "pattern": "Chưa xác định",
            "technical_status": "Chưa đủ dữ liệu lịch sử",
            "technical_score": 0,
            "technical_score_max": 100,
            "technical_score_breakdown": {
                "trend": {"score": 0, "max": 30, "reasons": ["Chưa đủ dữ liệu"]},
                "momentum": {"score": 0, "max": 25, "reasons": ["Chưa đủ dữ liệu"]},
                "volume": {"score": 0, "max": 20, "reasons": ["Chưa đủ dữ liệu"]},
                "structure": {"score": 0, "max": 25, "reasons": ["Chưa đủ dữ liệu"]},
            },
            "volume_analysis": "Chưa đủ dữ liệu để đánh giá volume",
            "darvas_breakout": False,
            "double_bottom": False,
            "spring_washout": False,
            "accumulation": False,
            "data_warnings": list(self.data_warnings),
            "data_points": len(self.df),
        }
        if self.df.empty or len(self.df) < 60:
            empty_result["data_warnings"].append("Cần tối thiểu 60 phiên hợp lệ để chấm điểm kỹ thuật")
            return empty_result

        darvas = self._detect_darvas_box()
        double_bottom = self._detect_double_bottom()
        spring = self._detect_spring_washout()
        accumulation = self._detect_accumulation()
        latest = self.df.iloc[-1]

        trend_score, trend_reasons = self._score_trend(latest)
        momentum_score, momentum_reasons = self._score_momentum(latest)
        volume_score, volume_reasons = self._score_volume()
        structure_score, structure_reasons = self._score_structure(
            darvas, double_bottom, spring, accumulation
        )

        total = int(np.clip(trend_score + momentum_score + volume_score + structure_score, 0, 100))
        pattern = (
            "Darvas Breakout" if darvas else
            "2 Đáy" if double_bottom else
            "Spring/Washout" if spring else
            "Accumulation" if accumulation else
            "Xu hướng tăng" if trend_score >= 22 else
            "Tích lũy/Sideway"
        )

        if total >= 75:
            status = "Xu hướng kỹ thuật mạnh"
        elif total >= 60:
            status = "Tích cực"
        elif total >= 45:
            status = "Trung tính"
        elif total >= 30:
            status = "Yếu"
        else:
            status = "Rất yếu"

        return {
            "pattern": pattern,
            "technical_status": status,
            "technical_score": total,
            "technical_score_max": 100,
            "technical_score_breakdown": {
                "trend": {"score": trend_score, "max": 30, "reasons": trend_reasons},
                "momentum": {"score": momentum_score, "max": 25, "reasons": momentum_reasons},
                "volume": {"score": volume_score, "max": 20, "reasons": volume_reasons},
                "structure": {"score": structure_score, "max": 25, "reasons": structure_reasons},
            },
            "volume_analysis": self._evaluate_volume_behavior(),
            "darvas_breakout": darvas,
            "double_bottom": double_bottom,
            "spring_washout": spring,
            "accumulation": accumulation,
            "data_warnings": list(self.data_warnings),
            "data_points": len(self.df),
            "latest_close": float(latest["close"]),
            "rsi14": round(float(latest["rsi14"]), 2) if self._valid(latest["rsi14"]) else None,
            "roc20": round(float(latest["roc20"]), 2) if self._valid(latest["roc20"]) else None,
            "volume_ratio": round(float(latest["volume"] / latest["vol_ma20"]), 2)
            if self._valid(latest["vol_ma20"]) and latest["vol_ma20"] > 0 else None,
        }

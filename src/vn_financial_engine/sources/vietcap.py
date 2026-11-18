"""Vietcap financial-statement adapter ported from the legacy price_api.py.

Keeps the existing source endpoint and canonical field mapping. The adapter
returns raw normalized statement rows; scoring/valuation never runs here.
"""
import logging
import hashlib
import json
import re
import time
import requests
import numpy as np
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def _fetch_bctc_ssi(symbol: str):
    symbol = str(symbol).upper().strip()
    if not symbol or not re.fullmatch(r"[A-Z0-9]{2,10}", symbol):
        logger.warning("[BCTC VCI] Mã cổ phiếu không hợp lệ: %r", symbol)
        return None

    CORE_IDS = {
        "IS_NET_REVENUE", "IS_COST_OF_GOODS_SOLD", "IS_NET_PROFIT_AFTER_TAX",
        "CF_NET_CASH_FLOWS_FROM_OPERATING_ACTIVITIES", "BS_TOTAL_ASSETS",
        "BS_SHORT_TERM_ASSETS", "BS_LONG_TERM_ASSETS", "BS_OWNERS_EQUITY",
        "BS_LIABILITIES"
    }

    base_url = "https://iq.vietcap.com.vn/api/iq-insight-service"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
        ),
        "Referer": "https://iq.vietcap.com.vn/",
        "Origin": "https://iq.vietcap.com.vn",
    }
    session = requests.Session()
    session.headers.update(headers)

    def get_json(path, params=None, retries=3):
        url = f"{base_url}{path}"
        last_error = None
        for attempt in range(retries):
            try:
                response = session.get(url, params=params, timeout=(8, 25))
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, (dict, list)):
                    raise ValueError("VCI trả về JSON không hợp lệ")
                return payload
            except Exception as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 2)
        raise RuntimeError(f"VCI API lỗi {path}: {last_error}") from last_error

    def unwrap(payload):
        if not isinstance(payload, dict):
            return payload
        data = payload.get("data", payload)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return data

    def get_period(row):
        year = (
            row.get("yearReport") or row.get("year")
            or row.get("year_report")
        )
        quarter = (
            row.get("quarter") or row.get("quarterReport")
            or row.get("quarter_report")
        )
        try:
            year = int(year)
            if quarter not in (None, ""):
                quarter = int(quarter)
            else:
                return None
            if not 1 <= quarter <= 4:
                return None
            return f"{year}-Q{quarter}"
        except (TypeError, ValueError):
            return None

    def canonical_id(report_name, field_code, title):
        import unicodedata

        label = str(title or field_code or "").strip().lower()
        label = "".join(
            ch for ch in unicodedata.normalize("NFD", label)
            if unicodedata.category(ch) != "Mn"
        ).replace("đ", "d")
        label = re.sub(r"[^a-z0-9]+", " ", label).strip()
        field = str(field_code).upper() if field_code else ""

        if report_name == "income_statement":
            if "doanh thu thuan" in label or "net revenue" in label:
                return "IS_NET_REVENUE"
            if "gia von hang ban" in label or "cost of goods sold" in label:
                return "IS_COST_OF_GOODS_SOLD"
            
            # ISA22 là LNST phân bổ cho cổ đông công ty mẹ, không phải
            # một bản ghi LNST hợp nhất độc lập; loại khỏi metric tổng LNST.
            if field == "ISA22" or "loi nhuan sau thue phan bo cho chu so huu" in label or "attributable to parent" in label:
                return None
            if field == "ISA20" or "loi nhuan sau thue thu nhap doanh nghiep" in label:
                return "IS_NET_PROFIT_AFTER_TAX"
            
            if field in ["IS_NET_PROFIT_AFTER_TAX", "IS_PROFIT_AFTER_TAX"] or "loi nhuan sau thue" in label:
                if "co dong thieu so" not in label and "khong kiem soat" not in label:
                    return "IS_NET_PROFIT_AFTER_TAX"

        elif report_name == "cash_flow":
            if field == "CFA18":
                return "CF_NET_CASH_FLOWS_FROM_OPERATING_ACTIVITIES"
            
            if "luu chuyen tien te rong" in label or "net cash flows from operating activities" in label:
                return "CF_NET_CASH_FLOWS_FROM_OPERATING_ACTIVITIES"

        elif report_name == "balance_sheet":
            if "tong cong tai san" in label or "tong tai san" in label or "total assets" in label:
                return "BS_TOTAL_ASSETS"
            if "tai san ngan han" in label or "current assets" in label:
                return "BS_SHORT_TERM_ASSETS"
            if "tai san dai han" in label or "non current assets" in label:
                return "BS_LONG_TERM_ASSETS"
            
            if "von chu so huu" in label or "owners equity" in label or "owner equity" in label:
                return "BS_OWNERS_EQUITY"
            if "von va cac quy" in label:
                return "BS_OWNERS_EQUITY"
                
            if "no phai tra" in label or "total liabilities" in label:
                return "BS_LIABILITIES"
        return None
    try:
        logger.info("[BCTC VCI] Bắt đầu lấy BCTC cho %s", symbol)

        metadata = {}
        try:
            meta = unwrap(get_json(
                f"/v1/company/{symbol}/financial-statement/metrics"
            ))
            if isinstance(meta, dict):
                for section in (
                    "INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW"
                ):
                    metadata[section] = {
                        str(item.get("field")): {
                            **item,
                            "resolved_title": (
                                item.get("titleVi")
                                or item.get("titleEn")
                                or item.get("field")
                            ),
                        }
                        for item in (meta.get(section) or [])
                        if isinstance(item, dict) and item.get("field")
                    }
        except Exception as meta_error:
            logger.warning(
                "[BCTC VCI] Không lấy được metadata %s: %s",
                symbol, meta_error
            )

        report_map = {
            "balance_sheet": "BALANCE_SHEET",
            "income_statement": "INCOME_STATEMENT",
            "cash_flow": "CASH_FLOW",
        }
        reports = {}
        latest_period = None
        retrieved_at = datetime.now(timezone.utc).isoformat()
        ignored_fields = {
            "organCode", "ticker", "createDate", "updateDate",
            "yearReport", "lengthReport", "publicDate", "quarter",
            "quarterReport", "year", "year_report", "length_report",
            "quarter_report",
        }

        for report_name, section in report_map.items():
            try:
                payload = unwrap(get_json(
                    f"/v1/company/{symbol}/financial-statement",
                    params={"section": section},
                ))
                if isinstance(payload, dict):
                    rows = (
                        payload.get("quarters")
                        or payload.get("quarter")
                        or []
                    )
                elif isinstance(payload, list):
                    rows = payload
                else:
                    rows = []

                records = []
                field_metadata = metadata.get(section, {})

                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    period = get_period(row)
                    if not period:
                        continue

                    if latest_period is None or period > latest_period:
                        latest_period = period

                    for field_code, raw_value in row.items():
                        if field_code in ignored_fields or raw_value is None:
                            continue
                        if isinstance(raw_value, (dict, list, bool)):
                            continue
                        try:
                            value = float(raw_value)
                        except (TypeError, ValueError):
                            continue
                        if not np.isfinite(value):
                            continue

                        meta_field = field_metadata.get(str(field_code), {})
                        title = meta_field.get("resolved_title", str(field_code))
                        item_id = canonical_id(report_name, field_code, title)
                        if not field_code:
                            continue
                        # Preserve unmapped source concepts for future sector metrics;
                        # never silently discard a reported line item.
                        if not item_id:
                            item_id = f"{report_name.upper()}:{field_code}"

                        if item_id == "IS_COST_OF_GOODS_SOLD" and value > 0:
                            value = -value

                        source_hash = hashlib.sha256(
                            json.dumps(row, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
                        ).hexdigest()
                        records.append({
                            "symbol": symbol,
                            "statement_type": report_name.upper(),
                            "source_hash": source_hash,
                            "source_provider": "VIETCAP",
                            "source_url": f"{base_url}/v1/company/{symbol}/financial-statement?section={section}",
                            "id": item_id,
                            "name": str(title),
                            "period": period,
                            "value": value,
                            "raw_value": raw_value,
                            "unit": "UNKNOWN",
                            "raw_unit": (
                                row.get("unit") or row.get("unitName")
                                or row.get("unit_name") or row.get("valueUnit")
                                or meta_field.get("unit") or meta_field.get("unitName")
                                or meta_field.get("unit_name") or meta_field.get("valueUnit")
                            ),
                            # Preserve the provider's full metric definition for
                            # later audited unit/scale normalization. Do not infer
                            # a normalized unit from undocumented metadata fields.
                            "source_field_metadata": meta_field,
                            "source_field": str(field_code),
                            "period_kind": "UNKNOWN",
                            "reporting_basis": "UNKNOWN",
                            "retrieved_at": retrieved_at,
                            "raw_period_fields": {
                                "yearReport": row.get("yearReport") or row.get("year"),
                                "quarter": row.get("quarter") or row.get("quarterReport"),
                                "lengthReport": row.get("lengthReport") or row.get("length_report"),
                            },
                        })

                if records:
                    unique_periods = sorted(list(set([item["period"] for item in records])), reverse=True)
                    keep_periods = set(unique_periods[:8])
                    records = [item for item in records if item["period"] in keep_periods]

                    reports[report_name] = records
                    logger.info(
                        "[BCTC VCI] %s | %s: %d chỉ tiêu, %d kỳ",
                        symbol, report_name, len(records),
                        len({item["period"] for item in records})
                    )
                else:
                    logger.warning(
                        "[BCTC VCI] %s | %s không có dữ liệu cốt lõi",
                        symbol, report_name
                    )

            except Exception as report_error:
                logger.warning(
                    "[BCTC VCI] %s | lỗi %s: %s",
                    symbol, report_name, report_error
                )

        if reports:
            reports["latest_period"] = latest_period or "Chưa xác định"
            reports["source"] = "VCI_DIRECT"
            reports["source_url"] = f"{base_url}/v1/company/{symbol}/financial-statement"
            reports["retrieved_at"] = retrieved_at
            reports["reporting_basis"] = "UNKNOWN"
            reports["period_kind"] = "UNKNOWN"
            logger.info(
                "[BCTC VCI] Hoàn tất %s | kỳ mới nhất: %s",
                symbol, reports["latest_period"]
            )
            return reports

        logger.error("[BCTC VCI] Không lấy được BCTC cho %s", symbol)
        return None

    except Exception as exc:
        logger.exception("[BCTC VCI] Lỗi lấy BCTC %s", symbol)
        return None

    finally:
        session.close()




def fetch_bctc_vietcap(symbol: str):
    """Public adapter entry point; legacy name retained for compatibility."""
    return _fetch_bctc_ssi(symbol)

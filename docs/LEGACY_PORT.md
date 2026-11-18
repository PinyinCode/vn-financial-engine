# Kế hoạch kế thừa mã cũ

Nguồn tham chiếu: `PinyinCode/se-verpricedemo`.

| Phần cũ | Phần mới | Trạng thái |
|---|---|---|
| `_fetch_bctc_ssi()` trong `price_api.py` | `sources/vietcap.py` | Đã port; giữ API VCI, map chỉ tiêu và lưu cả mã nguồn chưa map |
| `_fetch_history_ssi()` trong `price_api.py` | `sources/ssi.py` | Đã port theo SSI/Vnstock, chuẩn hóa OHLCV |
| `_fetch_one()` trong `price_api.py` | `sources/ssi.py` | Đã port snapshot 1 phút trong đúng ngày giao dịch |
| `ptkt.py` | `technical/analyzer.py` | Đã port baseline chỉ báo và thang điểm |
| Đơn vị từ Mongo cũ | `normalization/legacy.py` | Đã tạo cầu nối giá/EPS nghìn đồng và ratio phần trăm |
| Logic định giá/điểm cũ | `valuation/`, `scoring/` | Đang thay mới, không bê nguyên các ngưỡng cũ |

## Cảnh báo dữ liệu BCTC

Adapter Vietcap hiện đánh dấu `period_kind=UNKNOWN` và `reporting_basis=UNKNOWN` vì endpoint cũ chưa xác nhận được chắc chắn số liệu quý là độc lập hay lũy kế và chưa xác định rõ hợp nhất hay công ty mẹ. Do đó bộ tính TTM không được cộng các kỳ này. Chỉ sau khi xác minh schema nguồn hoặc bổ sung bộ chọn loại báo cáo, dữ liệu mới được gắn `STANDALONE_QUARTER`/`YTD` và `CONSOLIDATED`/`PARENT_ONLY`.

Đây là chốt an toàn bắt buộc: giữ nguyên cách lấy dữ liệu nhanh của mã cũ nhưng không kế thừa nhầm kỳ báo cáo hoặc nhầm cơ sở hợp nhất.

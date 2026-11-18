# VN Financial Engine

Engine độc lập cho dữ liệu tài chính, phân tích kỹ thuật, Screener và định giá cổ phiếu Việt Nam. Tái sử dụng các bộ lấy dữ liệu đã có trong dự án cũ; tập trung xây mới phần chuẩn hóa, metric, chấm điểm và định giá.

## Ưu tiên ngành
Ngân hàng, chứng khoán, thép, công nghệ, dầu khí, phân bón, sản xuất và bất động sản. Tạm bỏ nông nghiệp/thủy sản.

## Cấu trúc
```text
src/vn_financial_engine/
  sources/          Vietcap BCTC, SSI/Vnstock price
  normalization/    Unit bridge and period-safe normalization
  metrics/          DuPont, Piotroski, ROIC, WACC, FCFF, operating ratios
  technical/        Ported legacy technical analyzer
  scoring/          Sector-specific scorecards
  valuation/        Peer multiples, DCF, DDM, residual income
  ai/               Evidence-constrained analysis prompt
config/             Sector valuation profiles
tests/              Unit and regression tests
```

## Tính toàn vẹn dữ liệu
- Lưu nguồn, thời điểm tải, kỳ báo cáo, mã chỉ tiêu nguồn và cơ sở hợp nhất.
- Không cộng TTM nếu thiếu bốn quý liên tiếp độc lập.
- Không tự coi dữ liệu thiếu là 0; điểm phải kèm coverage.
- Mỗi phương pháp định giá phải công khai đầu vào, giả định và lý do loại trừ.
- Git lưu mã/config/tài liệu; dữ liệu BCTC khối lượng lớn sẽ lưu ở DB/object storage, không nhồi vào lịch sử Git.

## Tình trạng
Đang xây lõi phân tích. Chưa phải production: cần xác minh quy ước kỳ/cơ sở hợp nhất của nguồn BCTC, mapping metric theo từng ngành, kiểm thử trên báo cáo thực và backtest trước khi bật chấm điểm diện rộng.

Xem [phương pháp định giá](docs/METHODOLOGY.md) và [bản đồ kế thừa mã cũ](docs/LEGACY_PORT.md).

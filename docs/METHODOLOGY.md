# Phương pháp tài chính và định giá

## Nguyên tắc

- Không có một công thức định giá phù hợp mọi ngành.
- Chỉ chạy phương pháp khi đầu vào đủ, cùng đơn vị, cùng kỳ và cùng cơ sở hợp nhất.
- Giá trị ước tính phải giữ kết quả từng phương pháp, giả định, phương pháp bị loại và lý do.
- Không dùng điểm thiếu dữ liệu như điểm 0 rồi giả vờ dữ liệu đầy đủ.
- Ngưỡng chấm điểm hiện tại là cấu hình khởi đầu của engine, không phải chuẩn mực kế toán hay khuyến nghị đầu tư. Cần hiệu chỉnh bằng dữ liệu lịch sử và kiểm định ngoài mẫu.

## Các công thức chuẩn được triển khai

### Chất lượng và hiệu quả vốn
- DuPont 3 bước: ROE = biên lợi nhuận ròng × vòng quay tài sản × hệ số nhân vốn chủ.
- ROA = LNST / tài sản bình quân; ROE = LNST / vốn chủ bình quân.
- ROIC = NOPAT / vốn đầu tư bình quân; NOPAT = EBIT × (1 − thuế suất).
- CFO/NI, FCF, vòng quay tài sản, biên gộp/hoạt động/ròng.
- Piotroski F-Score 9 tiêu chí cho doanh nghiệp phi tài chính; từng tiêu chí thiếu được đánh dấu riêng.

### Chi phí vốn và DCF
- CAPM: Ke = Rf + beta × ERP.
- WACC dùng tỷ trọng giá trị thị trường của vốn chủ và nợ; chi phí nợ sau thuế.
- FCFF = EBIT(1 − T) + D&A − CapEx − thay đổi vốn lưu động ròng.
- FCFF DCF chiết khấu bằng WACC để ra EV, trừ nợ ròng, chia số cổ phiếu pha loãng để ra giá trị mỗi cổ phiếu.
- Gordon DDM: P0 = D1 / (Ke − g), chỉ khi Ke > g.
- Residual income cho ngân hàng: BVPS + (ROE − Ke) × BVPS / (Ke − g), hiện là mô hình một giai đoạn/cross-check.

### Định giá tương đối
- P/E × EPS, P/B × BVPS, P/S × doanh thu/cổ phiếu.
- EV/EBITDA phải tính EV từ EBITDA × multiple, trừ nợ ròng và chia số cổ phiếu pha loãng. Không lấy EBITDA/cổ phiếu nhân EV/EBITDA rồi gọi đó là giá trị vốn chủ.
- Graham √(22.5 × EPS × BVPS) chỉ dùng như cross-check cho doanh nghiệp phi tài chính có EPS và BVPS dương.
- Peer phải cùng ngành/mô hình kinh doanh, loại mẫu bất thường và lưu số lượng peer; tối thiểu 3 doanh nghiệp độc lập mới hiển thị thống kê peer.

## Mô hình theo ngành

- Ngân hàng: P/B, P/E, residual income, DDM; theo dõi ROE, NIM, NPL, bao phủ nợ xấu, CAR, CIR. Không dùng EV/EBITDA hay FCFF DCF như doanh nghiệp công nghiệp.
- Chứng khoán: P/B và P/E là trọng tâm; theo dõi ROE, vốn/tài sản, dư nợ margin/vốn chủ và biên hoạt động.
- Thép, phân bón, sản xuất: EV/EBITDA, P/E, P/B, FCFF; chú trọng chu kỳ biên lợi nhuận, tồn kho, nợ ròng/EBITDA, CFO và vốn lưu động.
- Công nghệ: tăng trưởng doanh thu, biên gộp, ROIC, FCF; kết hợp P/E, EV/EBITDA, P/S và DCF.
- Dầu khí: EV/EBITDA, P/E, P/B, DCF; kiểm tra chu kỳ hàng hóa, nợ ròng/EBITDA, khả năng trả lãi và CapEx.
- Bất động sản: P/B, NAV, P/E hoặc DDM tùy mô hình; cần tồn kho/dự án, presales, nợ và CFO. NAV chưa được bật cho tới khi có dữ liệu dự án đủ tin cậy.

## Các giới hạn hiện tại

- WACC, Ke, beta, ERP, tăng trưởng dài hạn và dự phóng phải được cung cấp từ bộ giả định có nguồn; engine không tự bịa.
- Residual income hiện là phiên bản một giai đoạn, cần bổ sung mô hình nhiều giai đoạn khi có dự phóng ROE/payout.
- Altman Z-Score không áp dụng máy móc cho ngân hàng và định chế tài chính.
- Ngưỡng điểm kỹ thuật được kế thừa từ bộ phân tích cũ; sẽ được kiểm định theo từng thị trường/ngành trước production.


## Chỉ báo rủi ro và peer group

- Altman Z-score có hai biến thể được định danh rõ: mô hình gốc cho doanh nghiệp sản xuất niêm yết và Z'' cho nhóm phi sản xuất. Không áp dụng cho ngân hàng/chứng khoán; ngưỡng gốc là ngưỡng lịch sử, không phải xác suất vỡ nợ đã hiệu chỉnh cho Việt Nam.
- Piotroski F-Score và Altman Z-score là chỉ báo sàng lọc bổ sung, không thay thế phân tích ngành hoặc chất lượng kiểm toán.
- Peer multiples lọc đúng ngành/nhóm so sánh, loại chính doanh nghiệp đang định giá, yêu cầu tối thiểu 3 peer hợp lệ. Khi có ít nhất 5 quan sát, áp dụng hàng rào 1.5×IQR; lưu lại mã bị loại và số lượng mẫu.
- DCF có ma trận nhạy cảm 3×3 theo WACC (±1 điểm %) và terminal growth (±0.5 điểm %). Ô không hợp lệ được để trống, không tự điều chỉnh giả định để ép ra kết quả.

## Scorecard ngành và phiên bản

Scorecard cơ bản dùng 50 điểm; định giá tương đối 30 điểm; kỹ thuật 20 điểm. Điểm cơ bản của từng ngành dùng các metric và trọng số khác nhau:
- Ngân hàng: ROE, tăng trưởng lợi nhuận, NPL, bao phủ nợ xấu, CAR, CIR.
- Chứng khoán: ROE, tăng trưởng, vốn/tài sản, dư nợ margin/vốn chủ, biên hoạt động.
- Thép/phân bón: biên gộp, ROIC, nợ ròng/EBITDA, CFO/NI, tăng trưởng, ngày tồn kho.
- Công nghệ: tăng trưởng doanh thu, biên gộp, ROIC, biên FCF, CFO/NI.
- Dầu khí: ROIC, nợ ròng/EBITDA, khả năng trả lãi, CFO/NI, tăng trưởng.
- Bất động sản: ROE, presales, CFO/NI, nợ/vốn chủ, tồn kho/tài sản.
- Sản xuất: ROE, ROIC, CFO/NI, nợ/vốn chủ, khả năng trả lãi.

Điểm số là thang đánh giá nội bộ theo ngưỡng cấu hình, không phải công thức học thuật chuẩn hóa. Khi thiếu dữ liệu, điểm không được bù bằng cách giả định số 0 hoặc nâng điểm các phần còn lại lên đủ 50; coverage phải đi kèm score. Mỗi kết quả lưu formula version để có thể tái lập lịch sử sau khi thay đổi công thức.

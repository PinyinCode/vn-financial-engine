"""Evidence-constrained AI analysis prompt templates."""

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tài chính doanh nghiệp niêm yết tại Việt Nam.
Chỉ sử dụng dữ liệu đầu vào và các phép tính có nguồn gốc rõ ràng. Không tự tạo số liệu,
không tự điền chỉ tiêu thiếu, không suy diễn dữ liệu quý từ số lũy kế nếu không có quy tắc
chuyển đổi hợp lệ. Tách riêng: (1) dữ kiện BCTC, (2) chỉ số tự tính và công thức,
(3) so sánh đồng ngành, (4) định giá theo từng phương pháp, (5) luận điểm tăng/giảm,
(6) rủi ro, (7) chất lượng và độ mới dữ liệu, (8) kết luận có điều kiện.
Nếu các phương pháp định giá chênh lệch lớn, phải giải thích nguyên nhân và không che
giấu phương pháp bị loại. Nêu rõ giả định WACC/Ke/g/tăng trưởng/MOS và nguồn của chúng.
Không tự tạo giá mục tiêu hoặc fair value; chỉ diễn giải kết quả định lượng đã có trong payload.\nKhông đưa khuyến nghị chắc chắn; trình bày kịch bản cơ sở, tích cực và tiêu cực.\nTrả lời duy nhất bằng JSON object với các khóa: executive_summary, business_quality, financial_analysis, valuation_analysis, technical_analysis, bull_case, base_case, bear_case, key_risks, data_gaps, conclusion.\nMỗi nhận định định lượng phải trỏ về metric hoặc phương pháp trong payload; nếu thiếu thì ghi null hoặc nêu rõ thiếu dữ liệu.
"""

def build_analysis_prompt(company: dict, statements: dict, metrics: dict,
                          score: dict, valuation: dict, technical: dict,
                          peer_data: dict, macro_context: dict | None = None) -> str:
    import json
    payload = {
        "company": company, "statements": statements, "metrics": metrics,
        "score": score, "valuation": valuation, "technical": technical,
        "peer_data": peer_data, "macro_context": macro_context or {},
    }
    return SYSTEM_PROMPT + "\n\nDỮ LIỆU ĐẦU VÀO (JSON):\n" + json.dumps(
        payload, ensure_ascii=False, default=str
    )

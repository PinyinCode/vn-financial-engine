from vn_financial_engine.ai.prompt import build_analysis_prompt


def test_ai_prompt_requires_evidence_linked_structured_output():
    prompt = build_analysis_prompt(
        {"symbol":"FPT"}, {}, {"roe":.15}, {}, {"fair_value":120},
        {"technical_score":70}, {},
    )
    assert "executive_summary" in prompt
    assert "Không tự tạo giá mục tiêu" in prompt
    assert "data_gaps" in prompt

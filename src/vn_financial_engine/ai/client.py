"""Configurable OpenAI-compatible LLM client; secrets are read only from environment."""
from __future__ import annotations

import json
import os
import requests


class AIAnalysisError(RuntimeError):
    pass


def run_analysis(prompt: str, timeout: int = 90) -> dict:
    api_key = os.getenv("AI_API_KEY") or os.getenv("ALIBABA_API_KEY")
    endpoint = os.getenv(
        "AI_API_URL",
        "https://ws-8lcqaxwxdv0h9xzy.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions",
    )
    model = os.getenv("AI_MODEL_NAME", "qwen3.7-max-2026-06-08")
    if not api_key:
        raise AIAnalysisError("Thiếu AI_API_KEY/ALIBABA_API_KEY")
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0.15,
            "messages": [
                {"role": "system", "content": "Phân tích dựa trên dữ liệu có nguồn; không bịa số."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    try:
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise TypeError("AI response must be a JSON object")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AIAnalysisError("AI trả về nội dung không phải JSON hợp lệ") from exc
    return {
        "model": model,
        "analysis": parsed,
        "usage": payload.get("usage", {}),
        "provider_response_id": payload.get("id"),
    }

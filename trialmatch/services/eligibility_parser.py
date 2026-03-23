"""
Eligibility criteria parsing service.

Uses a configurable instruct LLM (Hugging Face Inference Providers) to turn free-text
criteria into:
{
    "inclusion": [...],
    "exclusion": [...]
}
"""

from __future__ import annotations

import json
from typing import Any, Dict

from trialmatch.services.llm_models import get_reasoning_client


def parse_eligibility_criteria(criteria_text: str) -> Dict[str, Any]:
    """
    Parse free-text eligibility criteria into inclusion / exclusion lists via
    ``InferenceClient.chat_completion`` (Inference Providers, not legacy hf-inference).
    """
    criteria_trimmed = (criteria_text or "")[:8000]
    user_message = (
        "Read the following clinical trial eligibility criteria. Extract the main "
        'inclusion and exclusion rules as a JSON object with keys "inclusion" and '
        '"exclusion", each an array of short strings (one criterion per element). '
        "Respond with valid JSON only — no markdown fences or explanation.\n\n"
        f"Criteria:\n{criteria_trimmed}"
    )

    client = get_reasoning_client()
    completion = client.chat_completion(
        messages=[{"role": "user", "content": user_message}],
        max_tokens=512,
        temperature=0.1,
    )

    choices = getattr(completion, "choices", None) or []
    if not choices:
        return {"inclusion": [], "exclusion": []}
    choice0 = choices[0]
    message = choice0.message
    generated_text = (
        message.get("content", "")
        if isinstance(message, dict)
        else (getattr(message, "content", None) or "")
    )

    try:
        start = generated_text.find("{")
        end = generated_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"inclusion": [], "exclusion": []}
        json_str = generated_text[start : end + 1]
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"inclusion": [], "exclusion": []}


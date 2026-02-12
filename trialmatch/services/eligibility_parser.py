"""
Eligibility criteria parsing service.

Wraps the Phi-3 reasoning pipeline to turn free-text criteria into:
{
    "inclusion": [...],
    "exclusion": [...]
}
"""

from __future__ import annotations

import json
from typing import Dict, Any

from trialmatch.services.llm_models import get_reasoning_client


def parse_eligibility_criteria(criteria_text: str) -> Dict[str, Any]:
    """
    Use the Phi-3 reasoning pipeline to parse free-text eligibility criteria
    into inclusion / exclusion lists.
    """
    criteria_trimmed = (criteria_text or "")[:8000]
    prompt = (
        '[INST]Read the following eligibility criteria. Extract key inclusion/exclusion '
        'criteria as a JSON object with keys "inclusion" and "exclusion". Do not add '
        f'explanation. Criteria: "{criteria_trimmed}"[/INST]'
    )

    client = get_reasoning_client()
    # Hugging Face Inference API text-generation call
    generated_text = client.text_generation(
        prompt,
        max_new_tokens=512,
        stream=False,
    )

    try:
        json_str = generated_text[generated_text.find("{") : generated_text.rfind("}") + 1]
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"inclusion": [], "exclusion": []}


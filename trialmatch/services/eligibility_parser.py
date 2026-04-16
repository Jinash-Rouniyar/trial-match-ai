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
import re
from typing import Any, Dict

from trialmatch.services.llm_models import get_reasoning_client


_SECTION_SPLIT_RE = re.compile(
    r"(?im)^\s*(inclusion criteria|exclusion criteria)\s*:?\s*$"
)
_BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)]|[A-Za-z][.)])\s+")


def _normalize_criterion(line: str) -> str:
    cleaned = _BULLET_PREFIX_RE.sub("", line.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:;,\t")
    return cleaned


def _dedupe_keep_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for item in items:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def _extract_section_items(section_text: str) -> list[str]:
    items: list[str] = []
    for raw_line in (section_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"(?i)^(inclusion|exclusion)\s+criteria", line):
            continue
        normalized = _normalize_criterion(line)
        if normalized:
            items.append(normalized)
    return _dedupe_keep_order(items)


def _fast_parse_eligibility_criteria(criteria_text: str) -> Dict[str, Any] | None:
    text = (criteria_text or "").strip()
    if not text:
        return {"inclusion": [], "exclusion": []}

    matches = list(_SECTION_SPLIT_RE.finditer(text))
    if not matches:
        return None

    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        label = match.group(1).lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[label] = text[start:end].strip()

    inclusion = _extract_section_items(sections.get("inclusion criteria", ""))
    exclusion = _extract_section_items(sections.get("exclusion criteria", ""))

    if not inclusion and not exclusion:
        return None
    return {"inclusion": inclusion, "exclusion": exclusion}


def parse_eligibility_criteria(criteria_text: str) -> Dict[str, Any]:
    """
    Parse free-text eligibility criteria into inclusion / exclusion lists via
    ``InferenceClient.chat_completion`` (Inference Providers, not legacy hf-inference).
    """
    fast_parsed = _fast_parse_eligibility_criteria(criteria_text)
    if fast_parsed is not None:
        return fast_parsed

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
        max_tokens=192,
        temperature=0.0,
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


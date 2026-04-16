"""
Helpers for persisting trial eligibility parsing and criterion embeddings.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, Iterable, List

from trialmatch.config import settings
from trialmatch.services.db import trials_collection
from trialmatch.services.eligibility_parser import parse_eligibility_criteria
from trialmatch.services.matching_engine import get_embedding


def _criteria_hash(criteria_text: str) -> str:
    return hashlib.sha256((criteria_text or "").strip().encode("utf-8")).hexdigest()


def _cache_version() -> Dict[str, str]:
    return {
        "reasoning_model": settings.hf_reasoning_model,
        "embedding_model": settings.hf_embedding_model,
        "local_inference": "true" if settings.dev_local_inference else "false",
    }


def _normalized_strings(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in values or []:
        value = str(raw or "").strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        out.append(value)
    return out


def build_trial_cache(criteria_text: str) -> Dict[str, Any]:
    parsed = parse_eligibility_criteria(criteria_text)
    inclusion = _normalized_strings(parsed.get("inclusion") or [])
    exclusion = _normalized_strings(parsed.get("exclusion") or [])
    return {
        "criteria_hash": _criteria_hash(criteria_text),
        "cache_version": _cache_version(),
        "parsed_criteria": {
            "inclusion": inclusion,
            "exclusion": exclusion,
        },
        "criteria_embeddings": {
            "inclusion": [get_embedding(item).tolist() for item in inclusion],
            "exclusion": [get_embedding(item).tolist() for item in exclusion],
        },
        "prepared_at": datetime.now(timezone.utc).isoformat(),
    }


def is_trial_cache_fresh(trial_doc: Dict[str, Any]) -> bool:
    criteria = str(trial_doc.get("criteria") or "").strip()
    if not criteria:
        return False

    prepared_hash = str(trial_doc.get("criteria_hash") or "").strip()
    if prepared_hash != _criteria_hash(criteria):
        return False

    cached_version = trial_doc.get("cache_version") or {}
    return cached_version == _cache_version()


def ensure_trial_prepared(trial_doc: Dict[str, Any]) -> Dict[str, Any]:
    if is_trial_cache_fresh(trial_doc):
        return trial_doc

    criteria = str(trial_doc.get("criteria") or "").strip()
    cache_payload = build_trial_cache(criteria)
    trials_collection().update_one(
        {"nct_id": trial_doc["nct_id"]},
        {"$set": cache_payload},
    )
    updated = dict(trial_doc)
    updated.update(cache_payload)
    return updated

"""
Normalize ClinicalTrials.gov API-style study records for MongoDB storage.

Supports:
- Full JSON objects with ``protocolSection`` (ClinicalTrials.gov v2 shape)
- Legacy flat records: ``nct_id``, ``brief_title``, ``criteria``
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def extract_trial_input_list(payload: Any) -> Optional[List[Any]]:
    """
    Accept a top-level JSON array or an object with ``trials`` or ``studies`` (search API).
    """
    if isinstance(payload, list):
        return payload if payload else None
    if not isinstance(payload, dict):
        return None
    for key in ("trials", "studies"):
        value = payload.get(key)
        if isinstance(value, list) and value:
            return value
    return None


def normalize_trial_record(item: Any) -> Optional[Dict[str, str]]:
    """
    Return a document suitable for the ``trials`` collection, or ``None`` if unusable.
    """
    if not isinstance(item, dict):
        return None
    if isinstance(item.get("protocolSection"), dict):
        return _from_protocol_section(item)
    return _from_flat_record(item)


def _from_protocol_section(wrapper: Dict[str, Any]) -> Optional[Dict[str, str]]:
    ps = wrapper["protocolSection"]
    idm = ps.get("identificationModule") or {}
    nct = idm.get("nctId")
    if not nct:
        return None
    nct_id = str(nct).strip()
    if not nct_id:
        return None

    brief = idm.get("briefTitle") or idm.get("officialTitle") or ""
    brief_title = str(brief).strip() or nct_id

    elig = ps.get("eligibilityModule") or {}
    raw_criteria = elig.get("eligibilityCriteria")
    if raw_criteria is None:
        return None
    criteria = str(raw_criteria).strip()
    if not criteria:
        return None

    doc: Dict[str, str] = {
        "nct_id": nct_id,
        "brief_title": brief_title,
        "criteria": criteria,
    }
    sm = ps.get("statusModule") or {}
    overall = sm.get("overallStatus")
    if overall is not None and str(overall).strip():
        doc["overall_status"] = str(overall).strip()
    return doc


def _from_flat_record(item: Dict[str, Any]) -> Optional[Dict[str, str]]:
    nct_id = item.get("nct_id")
    brief_title = item.get("brief_title")
    criteria = item.get("criteria")
    if not (nct_id and brief_title and criteria):
        return None
    doc: Dict[str, str] = {
        "nct_id": str(nct_id).strip(),
        "brief_title": str(brief_title).strip(),
        "criteria": str(criteria).strip(),
    }
    if not doc["nct_id"] or not doc["brief_title"] or not doc["criteria"]:
        return None
    if "overall_status" in item and item.get("overall_status") is not None:
        doc["overall_status"] = str(item.get("overall_status") or "").strip()
    return doc

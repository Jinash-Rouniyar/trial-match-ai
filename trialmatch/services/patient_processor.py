"""
Patient profile extraction service.

This refactors the logic from the original scripts so we can work
directly from an in-memory Synthea JSON object (no filesystem writes
are required for the serverless backend).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from trialmatch.services.llm_models import get_ner_client


def _dedupe_keep_order(values: List[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(normalized)
    return ordered


def _patient_age_years(patient_data: Dict[str, Any]) -> int | None:
    birth_date_raw = str(patient_data.get("birthDate") or "").strip()
    if not birth_date_raw:
        return None
    try:
        birth_date = date.fromisoformat(birth_date_raw)
    except ValueError:
        return None
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def _condition_status_phrase(resource: Dict[str, Any]) -> str:
    clinical = resource.get("clinicalStatus") or {}
    codings = clinical.get("coding") or []
    codes = {
        str(item.get("code") or "").strip().lower()
        for item in codings
        if isinstance(item, dict)
    }
    abatement = str(resource.get("abatementDateTime") or "").strip()
    if "resolved" in codes or abatement:
        return "resolved"
    if "inactive" in codes:
        return "inactive"
    if "remission" in codes:
        return "in remission"
    if "active" in codes or "recurrence" in codes or "relapse" in codes:
        return "active"
    return "present"


def build_patient_profile_from_json(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a structured patient profile from a Synthea-style FHIR JSON document.

    Returns a dictionary of the form:
    {
        "conditions": [...],
        "medications": [...],
        "text_summary": "Patient has ...",
        "ner_entities": [...]
    }
    """
    if "entry" not in patient_data:
        return {}

    profile: Dict[str, Any] = {
        "conditions": [],
        "medications": [],
        "active_conditions": [],
        "resolved_conditions": [],
        "demographics": {},
        "text_summary": "",
    }
    full_text_narrative: List[str] = []

    gender = str(patient_data.get("gender") or "").strip().lower()
    age_years = _patient_age_years(patient_data)
    smoking_status = "never smoker"

    demographic_fragments: List[str] = []
    if age_years is not None:
        profile["demographics"]["age_years"] = age_years
        demographic_fragments.append(f"{age_years}-year-old")
    if gender:
        profile["demographics"]["gender"] = gender
        demographic_fragments.append(gender)
    if demographic_fragments:
        full_text_narrative.append(f"Patient is a {' '.join(demographic_fragments)}.")
    full_text_narrative.append(f"Patient is a {smoking_status}.")
    profile["demographics"]["smoking_status"] = smoking_status

    for entry in patient_data.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if resource_type == "Condition":
            condition_name = resource.get("code", {}).get("text", "")
            if condition_name:
                profile["conditions"].append(condition_name)
                condition_status = _condition_status_phrase(resource)
                if condition_status == "active":
                    profile["active_conditions"].append(condition_name)
                elif condition_status in {"resolved", "inactive", "in remission"}:
                    profile["resolved_conditions"].append(condition_name)
                full_text_narrative.append(
                    f"Patient has {condition_status} condition {condition_name}."
                )
        elif resource_type == "MedicationRequest":
            med_name = resource.get("medicationCodeableConcept", {}).get("text", "")
            if med_name:
                profile["medications"].append(med_name)
                status = str(resource.get("status") or "").strip().lower()
                status_text = status if status else "listed"
                full_text_narrative.append(
                    f"Patient has {status_text} medication {med_name}."
                )

    profile["conditions"] = _dedupe_keep_order(profile["conditions"])
    profile["active_conditions"] = _dedupe_keep_order(profile["active_conditions"])
    profile["resolved_conditions"] = _dedupe_keep_order(profile["resolved_conditions"])
    profile["medications"] = _dedupe_keep_order(profile["medications"])

    # Keep the summary compact but include the high-signal facts trials care about.
    if profile["active_conditions"]:
        full_text_narrative.append(
            "Active conditions include " + ", ".join(profile["active_conditions"]) + "."
        )
    if profile["resolved_conditions"]:
        full_text_narrative.append(
            "Resolved conditions include " + ", ".join(profile["resolved_conditions"]) + "."
        )
    if profile["medications"]:
        full_text_narrative.append(
            "Current or recent medications include " + ", ".join(profile["medications"]) + "."
        )

    profile["text_summary"] = " ".join(_dedupe_keep_order(full_text_narrative))

    if profile["text_summary"]:
        ner_client = get_ner_client()
        # Hugging Face Inference API - token classification
        entities = ner_client.token_classification(profile["text_summary"])
        profile["ner_entities"] = list(
            {entity["word"] for entity in entities if "word" in entity}
        )
    else:
        profile["ner_entities"] = []

    return profile


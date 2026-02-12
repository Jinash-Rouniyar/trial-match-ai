"""
Patient profile extraction service.

This refactors the logic from the original scripts so we can work
directly from an in-memory Synthea JSON object (no filesystem writes
are required for the serverless backend).
"""

from __future__ import annotations

from typing import Any, Dict, List

from trialmatch.services.llm_models import get_ner_client


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

    profile: Dict[str, Any] = {"conditions": [], "medications": [], "text_summary": ""}
    full_text_narrative: List[str] = []

    for entry in patient_data.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if resource_type == "Condition":
            condition_name = resource.get("code", {}).get("text", "")
            if condition_name:
                profile["conditions"].append(condition_name)
                full_text_narrative.append(f"Patient has a condition of {condition_name}.")
        elif resource_type == "MedicationRequest":
            med_name = resource.get("medicationCodeableConcept", {}).get("text", "")
            if med_name:
                profile["medications"].append(med_name)
                full_text_narrative.append(f"Patient is prescribed {med_name}.")

    profile["text_summary"] = " ".join(full_text_narrative)

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


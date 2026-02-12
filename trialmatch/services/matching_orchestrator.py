"""
High-level orchestration for running patient–trial matching.

This module ties together:
- patient profile (already stored in Mongo)
- trial loading (demo vs random)
- eligibility parsing (Phi-3 over HF Inference API)
- semantic scoring (BioLinkBERT over HF Inference API)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, List, Literal, Optional

from trialmatch.services.db import patients_collection, matches_collection
from trialmatch.services.trial_repository import (
    load_random_trials_data,
    load_target_trials_data,
)
from trialmatch.services.eligibility_parser import parse_eligibility_criteria
from trialmatch.services.matching_engine import calculate_match_score
from trialmatch.config import settings


MatchMode = Literal["demo", "random"]


def _get_patient_profile(patient_id: str) -> Optional[Dict[str, Any]]:
    doc = patients_collection().find_one({"patient_id": patient_id})
    if not doc:
        return None
    return doc.get("profile") or {}


def run_matching_for_patient(
    patient_id: str,
    mode: MatchMode = "demo",
    num_trials: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run the full matching pipeline for a single patient.

    Returns a document of the form:
    {
        "patient_id": "...",
        "mode": "...",
        "created_at": "...",
        "trials": [
            {"nct_id": "...", "title": "...", "score": 0-100},
            ...
        ],
    }
    """
    profile = _get_patient_profile(patient_id)
    if not profile:
        raise ValueError(f"Patient '{patient_id}' not found or has no profile.")

    # --- Select trials to analyze ---
    if mode == "demo":
        trials_df = load_target_trials_data()
    else:
        trials_df = load_random_trials_data(
            num_trials=num_trials or settings.num_random_trials
        )

    if trials_df is None or trials_df.empty:
        raise RuntimeError("No trials available for matching.")

    # --- Pre-parse criteria for all selected trials ---
    criteria_cache: Dict[str, Dict[str, Any]] = {}
    for _, trial in trials_df.iterrows():
        nct_id = trial["nct_id"]
        if nct_id in criteria_cache:
            continue
        criteria_cache[nct_id] = parse_eligibility_criteria(trial["criteria"])

    # --- Compute scores ---
    results: List[Dict[str, Any]] = []
    for nct_id, parsed_criteria in criteria_cache.items():
        if not parsed_criteria.get("inclusion"):
            continue
        score = calculate_match_score(profile, parsed_criteria)
        if score <= 0:
            continue

        title = trials_df[trials_df["nct_id"] == nct_id]["brief_title"].iloc[0]
        results.append(
            {
                "nct_id": nct_id,
                "title": title,
                "score": float(round(score, 2)),
            }
        )

    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)

    match_doc = {
        "patient_id": patient_id,
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trials": results,
    }

    matches_collection().insert_one(match_doc)
    # Convert ObjectId to string for API response
    match_doc["_id"] = str(match_doc.get("_id", ""))  # may be absent in memory
    return match_doc


def latest_matches_for_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the most recent match document for a patient, if any.
    """
    doc = (
        matches_collection()
        .find({"patient_id": patient_id})
        .sort("created_at", -1)
        .limit(1)
    )
    latest = next(iter(doc), None)
    if not latest:
        return None
    latest["_id"] = str(latest["_id"])
    return latest


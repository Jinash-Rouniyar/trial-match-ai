"""
Semantic matching core.

This module centralizes:
- Text embedding via BioLinkBERT
- Exclusion-first matching logic
- Percentage-based inclusion scoring
"""

from __future__ import annotations

from typing import Dict, Any, List

import numpy as np

from trialmatch.services.llm_models import get_embedding_client


def get_embedding(text: str) -> np.ndarray:
    """
    Compute a pooled embedding for the given text using BioLinkBERT via
    the Hugging Face Inference API (feature-extraction).
    """
    client = get_embedding_client()
    features = client.feature_extraction(text)
    arr = np.array(features, dtype=np.float32)
    # Shape may be [seq_len, hidden] or [1, seq_len, hidden]; reduce to 1D
    if arr.ndim == 3:
        arr = arr.mean(axis=1)
    if arr.ndim == 2:
        arr = arr.mean(axis=0)
    return arr


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def calculate_match_score(patient_profile: Dict[str, Any], trial_criteria: Dict[str, Any]) -> float:
    """
    Calculate a 0–100 match score between a patient profile and parsed trial criteria.

    Logic:
    1. If any exclusion criterion is semantically very similar to the patient summary,
       return 0 immediately.
    2. Otherwise, each sufficiently similar inclusion criterion contributes points
       towards a maximum score, which is normalized to 0–100.
    """
    score = 0.0
    max_possible_score = 0

    patient_full_text = patient_profile.get("text_summary", "")
    if not patient_full_text:
        return 0.0

    patient_embedding = get_embedding(patient_full_text)

    # --- Exclusion Criteria Check (Immediate Disqualification) ---
    exclusions: List[str] = trial_criteria.get("exclusion") or []
    for criterion in exclusions:
        criterion_embedding = get_embedding(criterion)
        if _cosine_similarity(patient_embedding, criterion_embedding) > 0.75:
            return 0.0

    # --- Inclusion Criteria Check (Point-Based Scoring) ---
    inclusions: List[str] = trial_criteria.get("inclusion") or []
    if inclusions:
        max_possible_score = len(inclusions) * 20
        if max_possible_score == 0:
            return 0.0

        for criterion in inclusions:
            criterion_embedding = get_embedding(criterion)
            similarity = _cosine_similarity(patient_embedding, criterion_embedding)
            if similarity > 0.6:
                score += 20

    if max_possible_score == 0:
        return 0.0

    return (score / max_possible_score) * 100.0


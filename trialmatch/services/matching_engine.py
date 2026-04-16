"""
Semantic matching core.

This module centralizes:
- Text embedding via BioLinkBERT
- Exclusion-aware matching logic
- Percentage-based inclusion scoring tuned for compact patient summaries
"""

from __future__ import annotations

from typing import Dict, Any, List, Sequence

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


def _as_embedding_array(values: Sequence[float] | np.ndarray) -> np.ndarray:
    return np.array(values, dtype=np.float32)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def calculate_match_score_from_precomputed(
    patient_embedding: np.ndarray,
    trial_criteria: Dict[str, Any],
) -> float:
    """
    Calculate a 0-100 match score using a precomputed patient embedding and trial
    criteria cache of the form:
    {
        "inclusion": [...],
        "exclusion": [...],
        "inclusion_embeddings": [[...], ...],
        "exclusion_embeddings": [[...], ...],
    }
    """
    score = 100.0

    exclusions: List[Sequence[float]] = trial_criteria.get("exclusion_embeddings") or []
    for embedding_values in exclusions:
        criterion_embedding = _as_embedding_array(embedding_values)
        # Be conservative about semantic exclusions. Compact patient summaries can look
        # spuriously similar to broad exclusion bullets such as "pregnancy" or "COPD".
        if _cosine_similarity(patient_embedding, criterion_embedding) > 0.82:
            return 0.0

    inclusions: List[Sequence[float]] = trial_criteria.get("inclusion_embeddings") or []
    if not inclusions:
        return 50.0

    strong_matches = 0
    for embedding_values in inclusions:
        criterion_embedding = _as_embedding_array(embedding_values)
        similarity = _cosine_similarity(patient_embedding, criterion_embedding)
        if similarity >= 0.68:
            strong_matches += 1
            continue
        if similarity >= 0.6:
            score -= 8.0
        else:
            score -= 15.0

    if strong_matches == 0:
        score -= 10.0

    return max(0.0, min(100.0, score))


def calculate_match_score(patient_profile: Dict[str, Any], trial_criteria: Dict[str, Any]) -> float:
    """
    Calculate a 0–100 match score between a patient profile and parsed trial criteria.

    Logic:
    1. If any exclusion criterion is semantically very similar to the patient summary,
       return 0 immediately.
    2. Otherwise, each sufficiently similar inclusion criterion contributes points
       towards a maximum score, which is normalized to 0–100.
    """
    patient_full_text = patient_profile.get("text_summary", "")
    if not patient_full_text:
        return 0.0

    patient_embedding = get_embedding(patient_full_text)
    exclusions: List[str] = trial_criteria.get("exclusion") or []
    inclusions: List[str] = trial_criteria.get("inclusion") or []
    precomputed = {
        "exclusion_embeddings": [get_embedding(criterion).tolist() for criterion in exclusions],
        "inclusion_embeddings": [get_embedding(criterion).tolist() for criterion in inclusions],
    }
    return calculate_match_score_from_precomputed(patient_embedding, precomputed)


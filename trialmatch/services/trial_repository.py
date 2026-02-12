"""
Trial loading and filtering helpers.

These wrap the logic from the original scripts for:
- Loading the two specific demo trials
- Loading a random subset of active trials
"""

from __future__ import annotations

import os
from typing import List, Optional

import pandas as pd

from trialmatch.config import settings
from trialmatch.services.db import trials_collection


TARGET_NCT_IDS: List[str] = ["NCT05943132", "NCT06241142"]


def _load_aact_tables() -> Optional[tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Load the core AACT subset tables from the configured directory.
    """
    studies_path = os.path.join(settings.aact_data_dir, "studies_subset.txt")
    elig_path = os.path.join(settings.aact_data_dir, "eligibilities_subset.txt")

    try:
        studies = pd.read_csv(
            studies_path,
            sep="|",
            low_memory=False,
            on_bad_lines="skip",
        )
        eligibilities = pd.read_csv(
            elig_path,
            sep="|",
            low_memory=False,
            on_bad_lines="skip",
        )
        return studies, eligibilities
    except FileNotFoundError:
        return None


def _load_trials_from_mongo(limit: Optional[int] = None) -> Optional[pd.DataFrame]:
    """
    Load trials stored in MongoDB via the admin upload flow.

    Expected schema per document:
    {
        "nct_id": str,
        "brief_title": str,
        "criteria": str,
        "overall_status": str (optional)
    }
    """
    coll = trials_collection()
    count = coll.count_documents({})
    if count == 0:
        return None

    cursor = coll.find({})
    if limit is not None:
        cursor = cursor.limit(limit)
    docs = list(cursor)
    if not docs:
        return None
    df = pd.DataFrame(docs)
    return df


def load_target_trials_data() -> Optional[pd.DataFrame]:
    """
    Load data for only the two demo target trials.
    """
    # Prefer admin-uploaded trials first
    mongo_df = _load_trials_from_mongo(limit=None)
    if mongo_df is not None and not mongo_df.empty:
        # For "demo" mode, just use whatever is in Mongo
        return mongo_df

    tables = _load_aact_tables()
    if tables is None:
        return None
    studies, eligibilities = tables

    target_studies_df = studies[studies["nct_id"].isin(TARGET_NCT_IDS)]
    target_eligibilities_df = eligibilities[eligibilities["nct_id"].isin(TARGET_NCT_IDS)]

    if target_studies_df.empty or target_eligibilities_df.empty:
        return None

    trials_to_analyze_df = pd.merge(target_studies_df, target_eligibilities_df, on="nct_id")
    return trials_to_analyze_df


def load_random_trials_data(num_trials: int) -> Optional[pd.DataFrame]:
    """
    Load a random subset of active trials (default configured in settings).
    """
    # Prefer admin-uploaded trials first
    mongo_df = _load_trials_from_mongo(limit=num_trials)
    if mongo_df is not None and not mongo_df.empty:
        return mongo_df

    tables = _load_aact_tables()
    if tables is None:
        return None
    studies, eligibilities = tables

    relevant_statuses = [
        "RECRUITING",
        "ACTIVE_NOT_RECRUITING",
        "ENROLLING_BY_INVITATION",
        "NOT_YET_RECRUITING",
    ]
    active_studies = studies[studies["overall_status"].isin(relevant_statuses)]
    if active_studies.empty:
        return None

    if len(active_studies) < num_trials:
        num_trials = len(active_studies)

    random_sample_df = active_studies.sample(n=num_trials)
    trials_to_analyze_df = pd.merge(random_sample_df, eligibilities, on="nct_id")
    return trials_to_analyze_df


"""
Trial loading from MongoDB (admin upload flow only).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from trialmatch.services.db import trials_collection


ACTIVE_STATUSES = {
    "RECRUITING",
    "ACTIVE_NOT_RECRUITING",
    "ENROLLING_BY_INVITATION",
    "NOT_YET_RECRUITING",
}


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
    return pd.DataFrame(docs)


def load_target_trials_data() -> Optional[pd.DataFrame]:
    """All trials in Mongo (matching mode ``demo``)."""
    return _load_trials_from_mongo(limit=None)


def load_random_trials_data(num_trials: int) -> Optional[pd.DataFrame]:
    """Sample recruiting-style trials from Mongo for matching mode ``random``."""
    trials_df = _load_trials_from_mongo(limit=None)
    if trials_df is None or trials_df.empty:
        return None

    if "overall_status" in trials_df.columns:
        active_df = trials_df[trials_df["overall_status"].isin(ACTIVE_STATUSES)]
    else:
        active_df = trials_df.iloc[0:0]
    source_df = active_df if not active_df.empty else trials_df
    sample_size = min(int(num_trials), len(source_df))
    if sample_size <= 0:
        return None
    return source_df.sample(n=sample_size).reset_index(drop=True)

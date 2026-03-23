"""
Trial loading from MongoDB (admin upload flow only).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from trialmatch.services.db import trials_collection


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
    """Up to ``num_trials`` trials from Mongo (matching mode ``random``; natural collection order)."""
    return _load_trials_from_mongo(limit=num_trials)

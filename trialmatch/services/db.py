"""
MongoDB helper utilities.

Provides a cached client + DB handle and convenience functions
for accessing the `patients` and `matches` collections.
"""

from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient

from trialmatch.config import settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """
    Lazily create a global MongoClient.
    """
    global _client
    if _client is None:
        if not settings.mongodb_uri:
            raise RuntimeError("MONGODB_URI is not configured.")
        _client = MongoClient(settings.mongodb_uri)
    return _client


def get_db():
    client = get_client()
    return client[settings.mongodb_db]


def patients_collection():
    return get_db()["patients"]


def matches_collection():
    return get_db()["matches"]


def trials_collection():
    return get_db()["trials"]


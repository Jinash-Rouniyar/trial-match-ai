"""
Centralized loading and caching of all LLM / embedding models.

We load:
- microsoft/Phi-3-mini-4k-instruct       -> reasoning_pipeline (eligibility parsing)
- michiyasunaga/BioLinkBERT-large       -> embedding_model + tokenizer
- d4data/biomedical-ner-all             -> ner_pipeline

Models are expensive to load, so we lazily initialize them once per
serverless container and cache them in module-level globals.
"""

from __future__ import annotations

from huggingface_hub import InferenceClient

from trialmatch.config import settings

_reasoning_client: InferenceClient | None = None
_embedding_client: InferenceClient | None = None
_ner_client: InferenceClient | None = None


def get_reasoning_client() -> InferenceClient:
    """
    Lazy getter for the Phi-3 reasoning client, backed by the Hugging Face
    Inference API (no local model weights are downloaded).
    """
    global _reasoning_client
    if _reasoning_client is None:
        _reasoning_client = InferenceClient(
            model="microsoft/Phi-3-mini-4k-instruct",
            token=settings.hf_token or None,
        )
    return _reasoning_client


def get_embedding_client() -> InferenceClient:
    """
    Lazy getter for the BioLinkBERT feature-extraction client.
    """
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = InferenceClient(
            model="michiyasunaga/BioLinkBERT-large",
            token=settings.hf_token or None,
        )
    return _embedding_client


def get_ner_client() -> InferenceClient:
    """
    Lazy getter for the biomedical NER client.
    """
    global _ner_client
    if _ner_client is None:
        _ner_client = InferenceClient(
            model="d4data/biomedical-ner-all",
            token=settings.hf_token or None,
        )
    return _ner_client


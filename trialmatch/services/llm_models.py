"""
Centralized loading and caching of all LLM / embedding models.

We load:
- Configurable instruct model (Inference Providers) -> eligibility parsing (chat completion)
- Configurable biomedical embedding model            -> embeddings (hf-inference router)
- d4data/biomedical-ner-all                          -> NER (hf-inference router)

Models are expensive to load, so we lazily initialize them once per
serverless container and cache them in module-level globals.
"""

from __future__ import annotations

import os

# Legacy serverless host returns 410; NER/embeddings use the hf-inference router path.
_DEFAULT_HF_INFERENCE_BASE = "https://router.huggingface.co/hf-inference"
if not os.environ.get("HF_INFERENCE_ENDPOINT", "").strip():
    os.environ["HF_INFERENCE_ENDPOINT"] = _DEFAULT_HF_INFERENCE_BASE

from huggingface_hub import InferenceClient

from trialmatch.config import settings

_reasoning_client: InferenceClient | None = None
_embedding_client: InferenceClient | None = None
_ner_client: InferenceClient | None = None


def get_reasoning_client() -> InferenceClient:
    """
    Chat LLM for eligibility parsing via Hugging Face Inference Providers
    (``provider=auto`` picks a deployed backend for the chosen model).

    ``microsoft/Phi-3-mini-4k-instruct`` is not deployed on ``hf-inference``; set
    ``HF_REASONING_MODEL`` / ``HF_LLM_PROVIDER`` in the environment instead.
    """
    global _reasoning_client
    if _reasoning_client is None:
        tok = settings.hf_token or None
        _reasoning_client = InferenceClient(
            provider=settings.hf_llm_provider,
            model=settings.hf_reasoning_model,
            token=tok,
        )
    return _reasoning_client


def get_embedding_client() -> InferenceClient:
    """
    Lazy getter for the biomedical feature-extraction client.
    """
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = InferenceClient(
            provider="hf-inference",
            model=settings.hf_embedding_model,
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
            provider="hf-inference",
            model="d4data/biomedical-ner-all",
            token=settings.hf_token or None,
        )
    return _ner_client


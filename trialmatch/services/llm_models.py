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
from types import SimpleNamespace
from typing import Any

# Legacy serverless host returns 410; NER/embeddings use the hf-inference router path.
_DEFAULT_HF_INFERENCE_BASE = "https://router.huggingface.co/hf-inference"
if not os.environ.get("HF_INFERENCE_ENDPOINT", "").strip():
    os.environ["HF_INFERENCE_ENDPOINT"] = _DEFAULT_HF_INFERENCE_BASE

from huggingface_hub import InferenceClient

from trialmatch.config import settings

_reasoning_client: InferenceClient | None = None
_embedding_client: InferenceClient | None = None
_ner_client: InferenceClient | None = None
_local_reasoning_client: Any | None = None
_local_embedding_client: Any | None = None
_local_ner_client: Any | None = None


def _local_model_id(model_name: str) -> str:
    """
    Convert provider-routed HF model ids to plain local model ids.

    Example:
      mistralai/Mistral-7B-Instruct-v0.2:featherless-ai
    -> mistralai/Mistral-7B-Instruct-v0.2
    """
    return (model_name or "").strip().split(":", 1)[0]


class _LocalReasoningClient:
    def __init__(self) -> None:
        try:
            import torch
            from transformers import AutoTokenizer, pipeline
        except ImportError as exc:
            raise RuntimeError(
                "DEV_LOCAL_INFERENCE is enabled, but local inference dependencies are "
                "missing. Install with: pip install transformers torch"
            ) from exc

        tok = settings.hf_token or None
        local_model_id = _local_model_id(settings.dev_local_reasoning_model)
        self._pipeline = pipeline(
            "text-generation",
            model=local_model_id,
            tokenizer=AutoTokenizer.from_pretrained(local_model_id, token=tok),
            token=tok,
            device=0 if torch.cuda.is_available() else -1,
        )

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.1,
    ) -> Any:
        user_text = "\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
        prompt = f"[INST]{user_text}[/INST]"
        outputs = self._pipeline(
            prompt,
            max_new_tokens=max_tokens,
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else None,
        )
        text = outputs[0].get("generated_text", "") if outputs else ""
        return SimpleNamespace(
            choices=[SimpleNamespace(message={"content": text})]
        )


class _LocalEmbeddingClient:
    def __init__(self) -> None:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "DEV_LOCAL_INFERENCE is enabled, but local inference dependencies are "
                "missing. Install with: pip install transformers torch"
            ) from exc

        self._torch = torch
        tok = settings.hf_token or None
        local_model_id = _local_model_id(settings.hf_embedding_model)
        self._tokenizer = AutoTokenizer.from_pretrained(local_model_id, token=tok)
        self._model = AutoModel.from_pretrained(local_model_id, token=tok)
        self._model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        self._model.eval()

    def feature_extraction(self, text: str) -> Any:
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
        with self._torch.no_grad():
            outputs = self._model(**inputs)
        return outputs.last_hidden_state.detach().cpu().tolist()


class _LocalNerClient:
    def __init__(self) -> None:
        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "DEV_LOCAL_INFERENCE is enabled, but local inference dependencies are "
                "missing. Install with: pip install transformers torch"
            ) from exc
        self._pipeline = pipeline(
            "ner",
            model="d4data/biomedical-ner-all",
            token=settings.hf_token or None,
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1,
        )

    def token_classification(self, text: str) -> Any:
        return self._pipeline(text)


def get_reasoning_client() -> InferenceClient:
    """
    Chat LLM for eligibility parsing via Hugging Face Inference Providers
    (``provider=auto`` picks a deployed backend for the chosen model).

    ``microsoft/Phi-3-mini-4k-instruct`` is not deployed on ``hf-inference``; set
    ``HF_REASONING_MODEL`` / ``HF_LLM_PROVIDER`` in the environment instead.
    """
    global _reasoning_client, _local_reasoning_client
    if settings.dev_local_inference:
        if _local_reasoning_client is None:
            _local_reasoning_client = _LocalReasoningClient()
        return _local_reasoning_client
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
    global _embedding_client, _local_embedding_client
    if settings.dev_local_inference:
        if _local_embedding_client is None:
            _local_embedding_client = _LocalEmbeddingClient()
        return _local_embedding_client
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
    global _ner_client, _local_ner_client
    if settings.dev_local_inference:
        if _local_ner_client is None:
            _local_ner_client = _LocalNerClient()
        return _local_ner_client
    if _ner_client is None:
        _ner_client = InferenceClient(
            provider="hf-inference",
            model="d4data/biomedical-ner-all",
            token=settings.hf_token or None,
        )
    return _ner_client


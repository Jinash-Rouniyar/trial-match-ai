from trialmatch.config import settings
from trialmatch.services import llm_models


def test_get_embedding_client_uses_configured_embedding_model(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setattr(llm_models, "InferenceClient", FakeClient)
    monkeypatch.setattr(settings, "hf_embedding_model", "NeuML/pubmedbert-base-embeddings")
    monkeypatch.setattr(settings, "hf_token", "hf_test")
    llm_models._embedding_client = None

    client = llm_models.get_embedding_client()
    assert isinstance(client, FakeClient)
    assert calls["provider"] == "hf-inference"
    assert calls["model"] == "NeuML/pubmedbert-base-embeddings"
    assert calls["token"] == "hf_test"


def test_get_reasoning_client_uses_configured_provider_and_model(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setattr(llm_models, "InferenceClient", FakeClient)
    monkeypatch.setattr(settings, "hf_llm_provider", "auto")
    monkeypatch.setattr(settings, "hf_reasoning_model", "mistralai/Mistral-7B-Instruct-v0.2")
    monkeypatch.setattr(settings, "hf_token", "hf_test")
    llm_models._reasoning_client = None

    client = llm_models.get_reasoning_client()
    assert isinstance(client, FakeClient)
    assert calls["provider"] == "auto"
    assert calls["model"] == "mistralai/Mistral-7B-Instruct-v0.2"
    assert calls["token"] == "hf_test"

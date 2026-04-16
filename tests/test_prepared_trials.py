import numpy as np

from trialmatch.services import prepared_trials


def test_build_trial_cache_deduplicates_and_embeds(monkeypatch):
    monkeypatch.setattr(
        prepared_trials,
        "parse_eligibility_criteria",
        lambda text: {
            "inclusion": ["Age 18+", "age 18+", "Diabetes"],
            "exclusion": ["Pregnant", "pregnant"],
        },
    )
    monkeypatch.setattr(
        prepared_trials,
        "get_embedding",
        lambda text: np.array([float(len(text)), 1.0], dtype=np.float32),
    )

    cache = prepared_trials.build_trial_cache("criteria text")

    assert cache["parsed_criteria"] == {
        "inclusion": ["Age 18+", "Diabetes"],
        "exclusion": ["Pregnant"],
    }
    assert len(cache["criteria_embeddings"]["inclusion"]) == 2
    assert len(cache["criteria_embeddings"]["exclusion"]) == 1
    assert cache["criteria_hash"]
    assert cache["prepared_at"]


def test_is_trial_cache_fresh_detects_matching_hash_and_version(monkeypatch):
    monkeypatch.setattr(prepared_trials.settings, "hf_reasoning_model", "reasoner")
    monkeypatch.setattr(prepared_trials.settings, "hf_embedding_model", "embedder")
    monkeypatch.setattr(prepared_trials.settings, "dev_local_inference", False)

    trial_doc = {
        "criteria": "criteria text",
        "criteria_hash": prepared_trials._criteria_hash("criteria text"),
        "cache_version": {
            "reasoning_model": "reasoner",
            "embedding_model": "embedder",
            "local_inference": "false",
        },
    }

    assert prepared_trials.is_trial_cache_fresh(trial_doc) is True


def test_ensure_trial_prepared_reuses_fresh_cache(monkeypatch):
    trial_doc = {
        "nct_id": "NCT1",
        "criteria": "criteria text",
        "criteria_hash": prepared_trials._criteria_hash("criteria text"),
        "cache_version": prepared_trials._cache_version(),
        "parsed_criteria": {"inclusion": ["A"], "exclusion": []},
        "criteria_embeddings": {"inclusion": [[1.0]], "exclusion": []},
    }

    def fail_build(_text):
        raise AssertionError("build_trial_cache should not be called for a fresh cache")

    monkeypatch.setattr(prepared_trials, "build_trial_cache", fail_build)

    assert prepared_trials.ensure_trial_prepared(trial_doc) == trial_doc

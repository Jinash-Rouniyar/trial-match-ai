import pandas as pd

from trialmatch.services import trial_repository


def test_load_random_trials_data_prefers_active_trials(monkeypatch):
    trials_df = pd.DataFrame(
        [
            {"nct_id": "NCT1", "overall_status": "COMPLETED"},
            {"nct_id": "NCT2", "overall_status": "RECRUITING"},
            {"nct_id": "NCT3", "overall_status": "NOT_YET_RECRUITING"},
        ]
    )

    monkeypatch.setattr(trial_repository, "_load_trials_from_mongo", lambda limit=None: trials_df)

    sampled = trial_repository.load_random_trials_data(2)

    assert sampled is not None
    assert set(sampled["nct_id"]) == {"NCT2", "NCT3"}


def test_load_random_trials_data_falls_back_when_status_missing(monkeypatch):
    trials_df = pd.DataFrame(
        [
            {"nct_id": "NCT1"},
            {"nct_id": "NCT2"},
        ]
    )

    monkeypatch.setattr(trial_repository, "_load_trials_from_mongo", lambda limit=None: trials_df)

    sampled = trial_repository.load_random_trials_data(1)

    assert sampled is not None
    assert len(sampled) == 1
    assert sampled.iloc[0]["nct_id"] in {"NCT1", "NCT2"}


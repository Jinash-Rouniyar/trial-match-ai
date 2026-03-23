from trialmatch.services.clinicaltrials_gov_import import (
    extract_trial_input_list,
    normalize_trial_record,
)


def test_extract_list_top_level_array():
    assert extract_trial_input_list([{"a": 1}]) == [{"a": 1}]


def test_extract_trials_and_studies_keys():
    assert extract_trial_input_list({"trials": [1]}) == [1]
    assert extract_trial_input_list({"studies": [2]}) == [2]


def test_extract_prefers_non_empty_list():
    assert extract_trial_input_list({"trials": [], "studies": [3]}) == [3]


def test_normalize_clinicaltrials_gov_minimal():
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT0001", "briefTitle": "A trial"},
            "eligibilityModule": {"eligibilityCriteria": "Inclusion:\n* age 18+\n"},
            "statusModule": {"overallStatus": "RECRUITING"},
        }
    }
    doc = normalize_trial_record(study)
    assert doc == {
        "nct_id": "NCT0001",
        "brief_title": "A trial",
        "criteria": "Inclusion:\n* age 18+",
        "overall_status": "RECRUITING",
    }


def test_normalize_clinicaltrials_gov_missing_eligibility_returns_none():
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT0003", "briefTitle": "X"},
        }
    }
    assert normalize_trial_record(study) is None


def test_normalize_flat_legacy():
    doc = normalize_trial_record(
        {
            "nct_id": "NCT9",
            "brief_title": "T",
            "criteria": "C",
            "overall_status": "COMPLETED",
        }
    )
    assert doc == {
        "nct_id": "NCT9",
        "brief_title": "T",
        "criteria": "C",
        "overall_status": "COMPLETED",
    }

from trialmatch.services import patient_processor


def test_build_patient_profile_includes_demographics_and_condition_status(monkeypatch):
    class DummyNerClient:
        def token_classification(self, _text):
            return [{"word": "asthma"}]

    monkeypatch.setattr(patient_processor, "get_ner_client", lambda: DummyNerClient())

    patient = {
        "birthDate": "2005-07-08",
        "gender": "female",
        "entry": [
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": "Childhood asthma (disorder)"},
                    "clinicalStatus": {"coding": [{"code": "resolved"}]},
                    "abatementDateTime": "2024-07-08T23:47:59-04:00",
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "medicationCodeableConcept": {
                        "text": "albuterol 0.83 MG/ML Inhalation Solution"
                    },
                }
            },
        ],
    }

    profile = patient_processor.build_patient_profile_from_json(patient)

    assert profile["demographics"]["gender"] == "female"
    assert profile["demographics"]["smoking_status"] == "never smoker"
    assert "Childhood asthma (disorder)" in profile["resolved_conditions"]
    assert "albuterol 0.83 MG/ML Inhalation Solution" in profile["medications"]
    assert "never smoker" in profile["text_summary"]
    assert "resolved condition Childhood asthma (disorder)" in profile["text_summary"]
    assert "active medication albuterol 0.83 MG/ML Inhalation Solution" in profile["text_summary"]


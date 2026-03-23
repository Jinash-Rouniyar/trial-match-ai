from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest

from app import app
from trialmatch.config import settings


@pytest.fixture
def client():
    settings.supabase_jwt_secret = "dummy_secret_for_testing"
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _token() -> str:
    payload = {
        "sub": "user_123",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        "user_metadata": {"role": "user"},
    }
    return jwt.encode(payload, "dummy_secret_for_testing", algorithm="HS256")


@patch("app.latest_matches_for_patient")
@patch("app.patients_collection")
def test_patient_report_pdf_handles_long_profile_content(mock_patients_collection, mock_latest, client):
    long_conditions = [
        "Seasonal allergic rhinitis (disorder)",
        "Medication review due (situation)",
    ] * 20
    long_meds = [
        "NDA020800 0.3 ML Epinephrine 1 MG/ML Auto-Injector",
        "Acetaminophen 325 MG / HYDROcodone Bitartrate 7.5 MG Oral Tablet",
    ] * 18
    summary = " ".join([f"Patient has a condition of item {i}." for i in range(40)])

    coll = MagicMock()
    coll.find_one.return_value = {
        "patient_id": "p1",
        "profile": {
            "conditions": long_conditions,
            "medications": long_meds,
            "text_summary": summary,
        },
    }
    mock_patients_collection.return_value = coll
    mock_latest.return_value = {
        "patient_id": "p1",
        "mode": "random",
        "created_at": "2026-01-01T00:00:00+00:00",
        "trials": [
            {"nct_id": "NCT1", "title": "Very long title " * 10, "score": 88.4},
            {"nct_id": "NCT2", "title": "Another long title " * 8, "score": 75.2},
        ],
    }

    response = client.get(f"/api/patient_report_pdf?patient_id=p1&token={_token()}")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    # Basic sanity check that endpoint produced a PDF instead of failing on formatting.
    assert response.data.startswith(b"%PDF")
    assert len(response.data) > 1000

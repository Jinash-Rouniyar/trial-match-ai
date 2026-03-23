import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app import app
from trialmatch.config import settings

@pytest.fixture
def client():
    # Set a dummy secret for testing
    settings.supabase_jwt_secret = "dummy_secret_for_testing"
    
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def generate_token(role="user", expired=False):
    payload = {
        "sub": "user_123",
        "user_metadata": {
            "role": role
        },
        "exp": datetime.now(timezone.utc) + timedelta(minutes=-10 if expired else 10),
        "aud": "authenticated"
    }
    return jwt.encode(payload, "dummy_secret_for_testing", algorithm="HS256")

def test_missing_token(client):
    # Call an endpoint that requires auth but no admin
    response = client.post("/api/patients_upload", json={})
    assert response.status_code == 401
    assert "Missing authorization token" in response.get_json()["error"]["message"]

def test_expired_token(client):
    token = generate_token(expired=True)
    response = client.post(
        "/api/patients_upload", 
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert "Token has expired" in response.get_json()["error"]["message"]

def test_valid_user_token_normal_route(client):
    token = generate_token(role="user")
    response = client.post(
        "/api/patients_upload", 
        json={}, # Missing patient data should return 400 from the route, but PASSes auth
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "must be a JSON object" in response.get_json()["error"]["message"]

def test_valid_user_token_admin_route_forbidden(client):
    token = generate_token(role="user")
    response = client.post(
        "/api/trials_upload", 
        json={"trials": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Admin privileges required" in response.get_json()["error"]["message"]

def test_valid_admin_token_admin_route(client):
    token = generate_token(role="admin")
    response = client.post(
        "/api/trials_upload",
        json={"trials": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    msg = response.get_json()["error"]["message"]
    assert "non-empty" in msg or "studies" in msg


def test_batch_match_requires_admin(client):
    token = generate_token(role="user")
    response = client.post(
        "/api/trials_match_batch",
        json={"patient_ids": ["p1"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "Admin privileges required" in response.get_json()["error"]["message"]

@patch("app.patients_collection")
def test_token_in_query_params(mock_patients_collection, client):
    """Avoid real Mongo: PDF route calls find_one; CI / local may have no server."""
    mock_coll = MagicMock()
    mock_coll.find_one.return_value = None
    mock_patients_collection.return_value = mock_coll

    token = generate_token(role="user")
    response = client.get(f"/api/patient_report_pdf?patient_id=test&token={token}")
    assert response.status_code == 404
    assert "Patient 'test' not found" in response.get_json()["error"]["message"]


@patch("app.run_matching_for_patient")
def test_trials_match_response_shape_demo_and_random(mock_run_matching, client):
    token = generate_token(role="user")

    def make_doc(pid: str, mode: str):
        return {
            "patient_id": pid,
            "mode": mode,
            "created_at": "2026-03-23T00:00:00+00:00",
            "trials": [
                {"nct_id": "NCT0001", "title": "Trial A", "score": 88.5},
                {"nct_id": "NCT0002", "title": "Trial B", "score": 73.0},
            ],
        }

    mock_run_matching.side_effect = lambda patient_id, mode, num_trials=None: make_doc(
        patient_id, mode
    )

    for mode in ("demo", "random"):
        response = client.post(
            "/api/trials_match",
            json={"patient_id": "p123", "mode": mode},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["patient_id"] == "p123"
        assert body["mode"] == mode
        assert isinstance(body["created_at"], str)
        assert isinstance(body["trials"], list)
        assert body["trials"][0]["nct_id"] == "NCT0001"
        assert isinstance(body["trials"][0]["score"], (int, float))

    assert mock_run_matching.call_count == 2

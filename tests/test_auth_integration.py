import pytest
import jwt
from datetime import datetime, timezone, timedelta
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
        json={"trials": []}, # Empty list returns 400 from route, but PASSes auth
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "must be a non-empty list" in response.get_json()["error"]["message"]

def test_token_in_query_params(client):
    token = generate_token(role="user")
    # patient_report_pdf can take token in URL
    response = client.get(f"/api/patient_report_pdf?patient_id=test&token={token}")
    # 404 because patient 'test' not found
    assert response.status_code == 404
    assert "Patient 'test' not found" in response.get_json()["error"]["message"]

import jwt
from datetime import datetime, timedelta, timezone

from trialmatch.config import settings
from trialmatch.services import auth


def _hs256_token(secret: str, role: str = "user") -> str:
    payload = {
        "sub": "u1",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        "user_metadata": {"role": role},
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_verify_supabase_jwt_hs256_success(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", "test_secret")
    token = _hs256_token("test_secret")
    decoded = auth.verify_supabase_jwt(token)
    assert decoded["sub"] == "u1"


def test_verify_supabase_jwt_requires_secret_for_hs256(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", "")
    token = _hs256_token("some_secret")
    try:
        auth.verify_supabase_jwt(token)
        assert False, "Expected InvalidTokenError"
    except jwt.InvalidTokenError as exc:
        assert "SUPABASE_JWT_SECRET is required" in str(exc)


def test_verify_supabase_jwt_unsupported_algorithm():
    token = jwt.encode({"sub": "u1"}, "x", algorithm="HS384")
    try:
        auth.verify_supabase_jwt(token)
        assert False, "Expected InvalidTokenError"
    except jwt.InvalidTokenError as exc:
        assert "Unsupported JWT algorithm" in str(exc)

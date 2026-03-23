import base64
import jwt
from functools import wraps
from typing import Optional

from jwt import PyJWKClient

from flask import request, jsonify, g

from trialmatch.config import settings

# Algorithms Supabase may use with asymmetric signing keys (JWKS).
_JWKS_ALGS = frozenset(
    {
        "RS256",
        "RS384",
        "RS512",
        "PS256",
        "PS384",
        "PS512",
        "ES256",
        "ES384",
        "ES512",
    }
)

_jwk_client: Optional[PyJWKClient] = None


def _error_response(message: str, status: int):
    return jsonify({"error": {"message": message, "status": status}}), status


def _auth_fully_disabled() -> bool:
    """Local dev escape hatch: no secret and no project URL → skip verification."""
    return not settings.supabase_jwt_secret.strip() and not settings.supabase_url.strip()


def _jwk_client_for_project() -> PyJWKClient:
    global _jwk_client
    if not settings.supabase_url.strip():
        raise jwt.InvalidTokenError(
            "SUPABASE_URL or VITE_SUPABASE_URL must be set on the backend to verify "
            "asymmetric (RS256/ES256, etc.) Supabase JWTs via JWKS."
        )
    jwks_url = f"{settings.supabase_url.strip().rstrip('/')}/auth/v1/.well-known/jwks.json"
    if _jwk_client is None:
        _jwk_client = PyJWKClient(jwks_url)
    return _jwk_client


def _decode_hs256(token: str) -> dict:
    if not settings.supabase_jwt_secret.strip():
        raise jwt.InvalidTokenError(
            "SUPABASE_JWT_SECRET is required to verify HS256 session tokens."
        )
    decode_kwargs = dict(algorithms=["HS256"], audience="authenticated")
    try:
        return jwt.decode(token, settings.supabase_jwt_secret, **decode_kwargs)
    except jwt.InvalidSignatureError:
        secret_bytes = base64.b64decode(settings.supabase_jwt_secret)
        return jwt.decode(token, secret_bytes, **decode_kwargs)


def _decode_with_jwks(token: str, alg: str) -> dict:
    jwk_client = _jwk_client_for_project()
    signing_key = jwk_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=[alg],
        audience="authenticated",
    )


def verify_supabase_jwt(token: str) -> dict:
    """
    Verify a Supabase Auth access token (HS256 with JWT secret, or asymmetric via JWKS).
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    try:
        header = jwt.get_unverified_header(token)
    except jwt.DecodeError as e:
        raise jwt.InvalidTokenError(str(e)) from e

    alg = header.get("alg")
    if not alg:
        raise jwt.InvalidTokenError("Missing alg in JWT header")

    if alg == "HS256":
        return _decode_hs256(token)
    if alg in _JWKS_ALGS:
        return _decode_with_jwks(token, alg)

    raise jwt.InvalidTokenError(
        f"Unsupported JWT algorithm {alg!r}. Use HS256 with SUPABASE_JWT_SECRET, or set "
        "SUPABASE_URL for asymmetric tokens (JWKS)."
    )


def require_auth(require_admin: bool = False):
    """
    Decorator that verifies the Supabase JWT.
    Checks inside Authorization header (Bearer token) or query string 'token'.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if _auth_fully_disabled():
                g.user_id = "anonymous"
                return view_func(*args, **kwargs)

            auth_header = request.headers.get("Authorization")
            token = None
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            if not token:
                token = request.args.get("token")

            if not token:
                return _error_response("Missing authorization token", 401)

            try:
                decoded = verify_supabase_jwt(token)
            except jwt.ExpiredSignatureError:
                return _error_response("Unauthorized: Token has expired", 401)
            except jwt.InvalidTokenError as e:
                return _error_response(f"Unauthorized: Invalid token ({str(e)})", 401)

            g.user_id = decoded.get("sub")

            role = (
                decoded.get("app_metadata", {}).get("role")
                or decoded.get("user_metadata", {}).get("role")
                or "user"
            )

            if require_admin and role != "admin":
                return _error_response("Forbidden: Admin privileges required", 403)

            return view_func(*args, **kwargs)
        return wrapper
    return decorator

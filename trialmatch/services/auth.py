import jwt
from functools import wraps
from flask import request, jsonify, g
from trialmatch.config import settings

def _error_response(message: str, status: int):
    return jsonify({"error": {"message": message, "status": status}}), status

def require_auth(require_admin: bool = False):
    """
    Decorator that verifies the Supabase JWT.
    Checks inside Authorization header (Bearer token) or query string 'token'.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # If no secret configured, just pass (useful for old local envs without Supabase)
            if not settings.supabase_jwt_secret:
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

            import base64

            decode_kwargs = dict(algorithms=["HS256"], audience="authenticated")
            decoded = None

            # Try the secret as-is first (plain string)
            try:
                decoded = jwt.decode(token, settings.supabase_jwt_secret, **decode_kwargs)
            except jwt.ExpiredSignatureError:
                return _error_response("Unauthorized: Token has expired", 401)
            except jwt.InvalidSignatureError:
                pass  # Try base64-decoded secret below
            except jwt.InvalidTokenError as e:
                return _error_response(f"Unauthorized: Invalid token ({str(e)})", 401)

            # Fallback: Supabase JWT secrets are often base64-encoded
            if decoded is None:
                try:
                    secret_bytes = base64.b64decode(settings.supabase_jwt_secret)
                    decoded = jwt.decode(token, secret_bytes, **decode_kwargs)
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

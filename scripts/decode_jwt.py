"""
Local utility: decode a Supabase JWT (not run by pytest).
Run: python scripts/decode_jwt.py
"""
import base64
import os

import jwt
from dotenv import load_dotenv

load_dotenv()
secret = os.getenv("SUPABASE_JWT_SECRET")

print("Testing decode...")
token = input("Paste your JWT here: ").strip()

try:
    print(f"Decoding with plain secret: {secret}")
    decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    print("Success with plain secret!", decoded)
except Exception as e:  # noqa: BLE001
    print(f"Failed plain: {e}")

try:
    print("Trying base64 decoded secret...")
    b64_secret = base64.b64decode(secret)
    decoded = jwt.decode(token, b64_secret, algorithms=["HS256"], audience="authenticated")
    print("Success with base64 decoded secret!", decoded)
except Exception as e:  # noqa: BLE001
    print(f"Failed b64: {e}")

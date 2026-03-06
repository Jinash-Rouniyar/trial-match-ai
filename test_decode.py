import jwt
import os
import base64
from dotenv import load_dotenv

load_dotenv()
secret = os.getenv("SUPABASE_JWT_SECRET")

# Test token decoding
print("Testing decode...")
token = input("Paste your JWT here: ").strip()

try:
    print(f"Decoding with plain secret: {secret}")
    decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    print("Success with plain secret!", decoded)
except Exception as e:
    print(f"Failed plain: {e}")

try:
    print("Trying base64 decoded secret...")
    b64_secret = base64.b64decode(secret)
    decoded = jwt.decode(token, b64_secret, algorithms=["HS256"], audience="authenticated")
    print("Success with base64 decoded secret!", decoded)
except Exception as e:
    print(f"Failed base64: {e}")

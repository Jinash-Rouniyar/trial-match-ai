import jwt
import os
from dotenv import load_dotenv

load_dotenv()
secret = os.getenv("SUPABASE_JWT_SECRET")
print(f"Secret: {secret}")

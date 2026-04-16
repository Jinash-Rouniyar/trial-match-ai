import os
from dataclasses import dataclass


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    """
    Central configuration for the backend.

    Values are read from environment variables with safe defaults where possible.
    """

    # Hugging Face token (Inference API / Inference Providers)
    hf_token: str = os.getenv("HF_TOKEN", "")

    hf_llm_provider: str = (os.getenv("HF_LLM_PROVIDER", "auto").strip() or "auto")
    hf_reasoning_model: str = (
        os.getenv("HF_REASONING_MODEL", "").strip()
        or "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"
    )
    # Hosted embedding model for semantic matching (must support feature-extraction).
    hf_embedding_model: str = (
        os.getenv("HF_EMBEDDING_MODEL", "").strip()
        or "NeuML/pubmedbert-base-embeddings"
    )
    # Dev-only switch: use local Transformers inference instead of HF hosted APIs.
    # Defaults to False so production behavior is unchanged.
    dev_local_inference: bool = _env_flag("DEV_LOCAL_INFERENCE", False)
    # Dev-only local reasoning model (used only when DEV_LOCAL_INFERENCE=true).
    dev_local_reasoning_model: str = (
        os.getenv("DEV_LOCAL_REASONING_MODEL", "").strip()
        or "microsoft/Phi-3-mini-4k-instruct"
    )

    # Local Synthea directory if used outside the API upload flow
    synthea_data_dir: str = os.getenv("SYNTHEA_DATA_DIR", "./synthea_data/json")

    # MongoDB
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_db: str = os.getenv("MONGODB_DB", "trialmatch")

    # Matching
    num_random_trials: int = int(os.getenv("NUM_RANDOM_TRIALS", "5"))

    # Supabase Auth (backend verifies JWTs from the Supabase JS client)
    # URL: optional here; frontend uses VITE_SUPABASE_URL. Backend accepts either env name.
    supabase_url: str = (
        os.getenv("SUPABASE_URL", "").strip()
        or os.getenv("VITE_SUPABASE_URL", "").strip()
    )
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")


settings = Settings()


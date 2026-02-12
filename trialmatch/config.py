import os
from dataclasses import dataclass


@dataclass
class Settings:
    """
    Central configuration for the backend.

    Values are read from environment variables with safe defaults where possible.
    """

    # Hugging Face token for loading Phi-3 and BioLinkBERT
    hf_token: str = os.getenv("HF_TOKEN", "")

    # Local data directories (AACT + Synthea)
    aact_data_dir: str = os.getenv("AACT_DATA_DIR", "./aact_data")
    synthea_data_dir: str = os.getenv("SYNTHEA_DATA_DIR", "./synthea_data/json")

    # MongoDB
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_db: str = os.getenv("MONGODB_DB", "trialmatch")

    # Matching
    num_random_trials: int = int(os.getenv("NUM_RANDOM_TRIALS", "5"))

    # Simple admin auth for project-level routes
    app_admin_secret: str = os.getenv("APP_ADMIN_SECRET", "")


settings = Settings()


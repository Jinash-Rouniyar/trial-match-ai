"""
Service layer for TrialMatch AI backend.

This module groups the core domain logic:
- LLM model lifecycle (`llm_models`)
- Patient profile extraction (`patient_processor`)
- Trial loading and filtering (`trial_repository`)
- Eligibility parsing (`eligibility_parser`)
- Match score computation (`matching_engine`)
- MongoDB persistence helpers (`db`)
"""


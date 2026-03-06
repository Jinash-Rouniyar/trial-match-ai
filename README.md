# TrialMatch AI

An AI-powered clinical trial matching system that parses synthetic patient EHRs and ranks relevant clinical trials using NLP and biomedical LLMs.

---

## Implementation Status

### ✅ Completed

| Component | Detail |
|---|---|
| **Patient FHIR Parsing** | Parses Synthea FHIR JSON (Condition, MedicationRequest) into a structured clinical profile, including a text narrative |
| **Biomedical NER** | Extracts named clinical entities from the patient narrative via `d4data/biomedical-ner-all` (Hugging Face Inference API) |
| **Eligibility Criteria Parsing** | Converts free-text trial criteria to structured `{"inclusion": [...], "exclusion": [...]}` JSON via `microsoft/Phi-3-mini-4k-instruct` |
| **Semantic Matching Engine** | Computes cosine similarity between patient and trial embeddings using `michiyasunaga/BioLinkBERT-large`; implements exclusion-first disqualification then inclusion scoring (0–100) |
| **Trial Repository** | Loads trials from MongoDB (admin-uploaded) or from AACT `.txt` flat files; supports demo (2 target NCT IDs) and random sampling modes |
| **MongoDB Persistence** | Stores patients, match results, and trials via `pymongo` |
| **REST API (Flask)** | `POST /api/patients_upload`, `GET /api/patients_index`, `GET /api/patient_detail`, `POST /api/trials_match`, `POST /api/trials_match_batch`, `POST /api/trials_upload` (admin), `GET /api/patient_report_pdf` |
| **PDF Report Generation** | Generates and streams a `reportlab` PDF of a patient's top matched trials |
| **Frontend UI Shell** | React + Vite + Tailwind app with pages: Landing, Dashboard (upload + cohort table), Patient Detail, Match Report, Admin upload panel |
| **Frontend API Client** | Typed Axios client (`client.ts`) wired to all backend endpoints via `VITE_API_BASE_URL` |
| **Unit Tests** | `pytest` tests covering exclusion disqualification and inclusion scoring logic |
| **Authentication** | Supabase integration for user accounts, sessions, and JWT-based backend authentication |
| **Role-Based Access Control** | Admin access is gated using Supabase `user_metadata.role` rather than a static token |

### ❌ Remaining / Not Yet Implemented

| Component | Detail |
|---|---|
| **Frontend ↔ Backend Production Connection** | Both are deployed independently but `VITE_API_BASE_URL` has not been configured on the frontend deployment, so API calls fail in production |
| **Integration & UAT Tests** | Only unit tests exist; no integration tests for the LLM pipeline or user acceptance test scenarios |

---

## Architecture

```
React Frontend (Vite + Tailwind)
        │  VITE_API_BASE_URL
        ▼
Flask REST API  ──── MongoDB Atlas
        │
   trialmatch/ services
   ├── patient_processor.py   (FHIR → profile + NER)
   ├── eligibility_parser.py  (Phi-3 → inclusion/exclusion JSON)
   ├── matching_engine.py     (BioLinkBERT → cosine score)
   ├── matching_orchestrator.py
   ├── trial_repository.py    (AACT flat files or MongoDB)
   └── llm_models.py          (lazy HF InferenceClient singletons)
```

---

## Environment Variables

**Backend:**

| Variable | Description |
|---|---|
| `HF_TOKEN` | Hugging Face token (required for model inference) |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | Database name (default: `trialmatch`) |
| `AACT_DATA_DIR` | Path to AACT subset files (default: `./aact_data`) |
| `NUM_RANDOM_TRIALS` | Random trial sample size (default: `5`) |
| `APP_ADMIN_SECRET` | Static token protecting `/api/trials_upload` |

**Frontend:**

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL (e.g. `https://your-backend.vercel.app`) |

> ⚠️ **Production gap**: `VITE_API_BASE_URL` must be set on the frontend Vercel deployment to connect the frontend to the backend. This has not been done yet.

---

## Local Development

**Backend:**
```bash
cd trial-match-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Place studies_subset.txt + eligibilities_subset.txt under aact_data/
export HF_TOKEN=... MONGODB_URI=...
export FLASK_APP=app.py && flask run
```

**Frontend:**
```bash
cd trial-match-ai/frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:5000" > .env.local
npm run dev
```

**Tests:**
```bash
pytest
```

---

## Key API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/patients_upload` | Upload Synthea FHIR JSON, build + store profile |
| `GET` | `/api/patients_index` | List all patients |
| `GET` | `/api/patient_detail` | Patient profile + latest match results |
| `POST` | `/api/trials_match` | Run matching for one patient |
| `POST` | `/api/trials_match_batch` | Run matching for multiple patients |
| `POST` | `/api/trials_upload` | Upload trials (requires `X-Admin-Token` header) |
| `GET` | `/api/patient_report_pdf` | Download PDF summary of latest match |

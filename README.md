# TrialMatch AI

An AI-powered clinical trial matching system that parses synthetic patient EHRs and ranks relevant clinical trials using NLP and biomedical LLMs.

---

## Implementation Status

### Completed

| Component | Detail |
|---|---|
| **Patient FHIR Parsing** | Synthea FHIR JSON (Condition, MedicationRequest) → structured profile + narrative |
| **Biomedical NER** | `d4data/biomedical-ner-all` via Hugging Face Inference API |
| **Eligibility parsing** | Configurable instruct LLM via **Inference Providers** (`chat_completion`; default `mistralai/Mistral-7B-Instruct-v0.2`) → inclusion/exclusion JSON |
| **Semantic matching** | PubMedBERT-family embeddings (default `NeuML/pubmedbert-base-embeddings`), exclusion-first then inclusion scoring (0–100) |
| **Trial storage** | MongoDB `trials` collection only (no AACT flat files in the app) |
| **Trial upload** | Admin API accepts **ClinicalTrials.gov v2** (`protocolSection`) or **legacy flat** rows; supports `trials` / `studies` wrappers |
| **MongoDB** | `patients`, `matches`, `trials` |
| **REST API** | Flask routes under `/api/...` (see below) |
| **PDF reports** | `reportlab` download of latest match summary |
| **Frontend** | Vite + React + Tailwind; Supabase Auth; Axios + `VITE_API_BASE_URL` |
| **Auth / RBAC** | Supabase session JWT; Flask verifies **HS256** with `SUPABASE_JWT_SECRET` or **asymmetric** (e.g. RS256) via JWKS when `SUPABASE_URL` is set. Admin routes require `role: admin` in JWT metadata |
| **Tests** | `pytest`: matching engine, ClinicalTrials.gov import helpers, auth integration |

### Remaining / gaps

| Item | Detail |
|---|---|
| **Production wiring** | Set `VITE_API_BASE_URL` on the deployed frontend so it reaches the backend |
| **Supabase admin role** | Ensure real admins get `role: admin` in JWT (e.g. Supabase dashboard / triggers), not only at signup metadata |
| **Integration / UAT** | No automated tests hitting live HF / Mongo for full pipeline |

---

## Architecture

```
React (Vite)  ── VITE_API_BASE_URL ──►  Flask /api
     │                                      │
  Supabase Auth                              MongoDB
  (access_token → Bearer)                    (patients, trials, matches)

trialmatch/services
├── patient_processor.py
├── clinicaltrials_gov_import.py  ← CT.gov JSON → flat trial docs
├── eligibility_parser.py
├── matching_engine.py
├── matching_orchestrator.py
├── trial_repository.py            ← Mongo only
├── auth.py                        ← Supabase JWT verify
└── llm_models.py
```

---

## Environment Variables

### Backend (`.env` in repo root is loaded by `app.py` via `python-dotenv`)

| Variable | Description |
|---|---|
| `HF_TOKEN` | Hugging Face user access token (required for NER, embeddings, and routed LLM calls) |
| `HF_REASONING_MODEL` | Hub model id for eligibility parsing (must have an [Inference Provider](https://huggingface.co/models?inference=warm) when using `HF_LLM_PROVIDER=auto`). Default: **`mistralai/Mistral-7B-Instruct-v0.2`**. **`Mistral-7B-Instruct-v0.1`** is not listed as deployed by Inference Providers on its model card—use **v0.2** / **v0.3** for hosted routing, or set v0.1 only if you call a **self-hosted** compatible endpoint. Alternatives: Llama / Qwen instruct ids, optionally with a provider suffix (e.g. `:novita`) if your HF routing setup requires it. |
| `HF_LLM_PROVIDER` | Optional. `auto` (default) lets Hugging Face pick a provider for that model; or set a named provider (`together`, `groq`, `featherless-ai`, …). See [Inference Providers](https://huggingface.co/docs/inference-providers/index). |
| `HF_EMBEDDING_MODEL` | Hosted embedding model id for semantic matching. Must support `feature-extraction` on your provider. Default: **`NeuML/pubmedbert-base-embeddings`**. A second validated biomedical option is `pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb`. |
| `HF_INFERENCE_ENDPOINT` | Optional. Used for **NER** and **embedding feature-extraction**. Defaults to `https://router.huggingface.co/hf-inference`. Legacy `api-inference.huggingface.co` is retired. |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | Database name (default: `trialmatch`) |
| `NUM_RANDOM_TRIALS` | Cap for `mode=random` sample size (default: `5`) |
| `SUPABASE_JWT_SECRET` | **JWT secret** from Supabase (Settings → API). Required to verify **HS256** access tokens. |
| `SUPABASE_URL` or `VITE_SUPABASE_URL` | **Required on the backend** if your project uses **asymmetric** JWT signing keys: Flask loads JWKS from `{url}/auth/v1/.well-known/jwks.json`. Also used by the frontend as `VITE_SUPABASE_URL`. |

If both `SUPABASE_JWT_SECRET` and `SUPABASE_URL` are unset, the API skips JWT verification (local dev only).

### Frontend (`.env.local`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL, e.g. `http://127.0.0.1:5000` |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |

---

## Local development

**Backend:**

```bash
cd trial-match-ai
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# .env: HF_TOKEN, MONGODB_URI, SUPABASE_JWT_SECRET (recommended), HF_REASONING_MODEL if you change the default LLM
python app.py
# or: flask run
```

**Frontend:**

```bash
cd trial-match-ai/frontend
npm install
# .env.local: VITE_API_BASE_URL, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
npm run dev
```

**Tests** (from repo root):

```bash
python -m pytest
```

---

## Key API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/patients_upload` | User JWT | Upload Synthea FHIR JSON |
| `GET` | `/api/patients_index` | User JWT | List patients |
| `GET` | `/api/patient_detail` | User JWT | Profile + latest match |
| `POST` | `/api/trials_match` | User JWT | Match one patient |
| `POST` | `/api/trials_match_batch` | **Admin JWT** | Match many patients |
| `POST` | `/api/trials_upload` | **Admin JWT** | Upload trials (CT.gov JSON or flat); body = array or `{ trials }` / `{ studies }` |
| `GET` | `/api/patient_report_pdf` | User JWT (or `token` query) | PDF summary |

**Trials upload body:** JSON array of studies, or `{ "trials": [ ... ] }` / `{ "studies": [ ... ] }`. Each element: either **ClinicalTrials.gov v2** (`protocolSection…`) or **flat** `{ nct_id, brief_title, criteria, overall_status? }`. Response: `{ "upserted", "skipped" }`.

---

## Deployment (high level)

- Deploy Flask + `trialmatch/` with backend env vars.
- Deploy static frontend; set `VITE_API_BASE_URL` to the backend URL.
- Configure Supabase redirect URLs and JWT secret on the server.

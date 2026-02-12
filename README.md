## TrialMatch AI – Full Stack App

This repo contains:

- **Backend**: a Flask app in `app.py` exposing REST endpoints under `/api/...`
- **Core Python services** under `trialmatch/`
- **Frontend** React app under `frontend/`

### Environment Variables

Backend:

- `HF_TOKEN` – Hugging Face access token with permission to call the Inference API.
- `AACT_DATA_DIR` – Path to AACT subset files inside the deployment (default `./aact_data`).
- `SYNTHEA_DATA_DIR` – Path to Synthea JSONs if used locally (not required for API upload mode).
- `MONGODB_URI` – MongoDB connection string (e.g. Atlas).
- `MONGODB_DB` – MongoDB database name (default `trialmatch`).
- `NUM_RANDOM_TRIALS` – Optional, number of random trials when using `mode="random"` (default `5`).
- `APP_ADMIN_SECRET` – Optional admin token used to protect admin routes like `/api/trials_upload`.

Frontend (Vercel project that hosts the React app):

- `VITE_API_BASE_URL` – Base URL pointing at the backend deployment, e.g. `https://your-backend.vercel.app`.

### Backend Setup (local dev)

1. `cd trial-match-ai`
2. Create and activate a Python virtualenv.
3. `pip install -r requirements.txt`
4. Place `studies_subset.txt` and `eligibilities_subset.txt` under `aact_data/`.
5. Export environment variables (at minimum `HF_TOKEN`, `MONGODB_URI`).
6. Run the Flask dev server:

   ```bash
   export FLASK_APP=app.py
   flask run
   ```

### Frontend Setup (local dev)

1. `cd trial-match-ai/frontend`
2. `npm install`
3. Create `.env.local` with:

   ```bash
   VITE_API_BASE_URL=http://localhost:3000
   ```

   (or the URL of your deployed backend)

4. `npm run dev` and open the printed URL.

### Key API Flows

- **Upload patients**
  - `POST /api/patients_upload` – body `{ "patient": { ...synthea json... }, "patient_id"?: "optional-id" }`
  - `GET /api/patients_index` – list of patients for the dashboard.
  - `GET /api/patient_detail?patient_id=...` – full profile + latest match.

- **Run matching**
  - `POST /api/trials_match` – single-patient matching.
  - `POST /api/trials_match_batch` – body `{ "patient_ids": [...], "mode": "demo"|"random", "num_trials"?: number }` to run matching for many patients in one call.

- **Admin trials upload**
  - `POST /api/trials_upload` – body `{ "trials": [ { "nct_id", "brief_title", "criteria", "overall_status"?: string }, ... ] }`
  - Requires header `X-Admin-Token: $APP_ADMIN_SECRET` when `APP_ADMIN_SECRET` is set.

- **PDF reports**
  - `GET /api/patient_report_pdf?patient_id=...` – returns a simple PDF summary of the latest match for the given patient.

### Testing

- Backend tests use `pytest`:

```bash
pytest
```

The sample tests under `tests/` cover core matching logic (exclusion vs inclusion scoring) and can be extended for other modules.

### Deployment (high level)

- **Backend**:
  - Deploy `app.py` and the `trialmatch/` package to your hosting provider.
  - Configure the backend environment variables (`HF_TOKEN`, `MONGODB_URI`, etc.).
  - Ensure the backend is reachable under a base URL like `https://your-backend.example.com`.

- **Frontend**:
  - Deploy the React app from `frontend/` (e.g. Vercel / any static host).
  - Set `VITE_API_BASE_URL` to the backend’s base URL.
  - Build command: `npm run build`, output directory: `dist`.


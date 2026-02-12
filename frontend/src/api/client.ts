import axios from "axios";

export const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  }
});

export interface PatientSummary {
  patient_id: string;
  created_at?: string;
  conditions: string[];
}

export interface PatientProfile {
  conditions: string[];
  medications: string[];
  text_summary: string;
  ner_entities: string[];
}

export interface TrialMatch {
  nct_id: string;
  title: string;
  score: number;
}

export interface MatchDocument {
  patient_id: string;
  mode: string;
  created_at: string;
  trials: TrialMatch[];
}

export async function uploadPatient(patient: unknown, patientId?: string) {
  const res = await api.post("/api/patients_upload", {
    patient,
    patient_id: patientId
  });
  return res.data as { patient_id: string; profile: PatientProfile };
}

export async function listPatients() {
  const res = await api.get("/api/patients_index");
  return res.data as { patients: PatientSummary[] };
}

export async function fetchPatientDetail(patientId: string) {
  const res = await api.get(`/api/patient_detail?patient_id=${encodeURIComponent(patientId)}`);
  return res.data as {
    patient_id: string;
    created_at?: string;
    profile: PatientProfile;
    latest_matches?: MatchDocument | null;
  };
}

export async function runMatching(patientId: string, mode: "demo" | "random", numTrials?: number) {
  const res = await api.post("/api/trials_match", {
    patient_id: patientId,
    mode,
    num_trials: numTrials
  });
  return res.data as MatchDocument;
}

export async function runBatchMatching(
  patientIds: string[],
  mode: "demo" | "random",
  numTrials?: number
) {
  const res = await api.post("/api/trials_match_batch", {
    patient_ids: patientIds,
    mode,
    num_trials: numTrials
  });
  return res.data as { results: Array<{ patient_id: string; mode?: string; created_at?: string; trials?: TrialMatch[]; error?: string }> };
}

export async function uploadTrials(
  trials: Array<{ nct_id: string; brief_title: string; criteria: string; overall_status?: string }>,
  adminToken?: string
) {
  const res = await api.post(
    "/api/trials_upload",
    { trials },
    {
      headers: adminToken
        ? {
            "X-Admin-Token": adminToken
          }
        : {}
    }
  );
  return res.data as { upserted: number };
}

export function getPatientReportPdfUrl(patientId: string): string {
  const encoded = encodeURIComponent(patientId);
  return `${baseURL}/api/patient_report_pdf?patient_id=${encoded}`;
}


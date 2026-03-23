import axios, { type AxiosError } from "axios";
import { supabase } from "./supabaseClient";

export const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  }
});

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
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

export async function listPatients(options?: { signal?: AbortSignal }) {
  const res = await api.get("/api/patients_index", { signal: options?.signal });
  return res.data as { patients: PatientSummary[] };
}

export async function fetchPatientDetail(patientId: string, options?: { signal?: AbortSignal }) {
  const res = await api.get(`/api/patient_detail?patient_id=${encodeURIComponent(patientId)}`, {
    signal: options?.signal,
  });
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

/**
 * POST the JSON as returned from ClinicalTrials.gov: a top-level array of studies,
 * or an object with a non-empty `trials` or `studies` list (see server-side
 * `extract_trial_input_list`). Avoid wrapping in `{ trials }` here so payloads like
 * `{ "trials": [], "studies": [...] }` are handled correctly.
 */
export async function uploadTrials(payload: unknown) {
  const res = await api.post("/api/trials_upload", payload);
  return res.data as { upserted: number; skipped?: number };
}

export function getApiErrorMessage(
  err: unknown,
  fallback = "Something went wrong. Try again."
): string {
  const ax = err as AxiosError<{ error?: { message?: string } }>;
  const msg = ax.response?.data?.error?.message;
  return typeof msg === "string" ? msg : fallback;
}

/** True when the API rejected the request as unauthenticated (invalid or missing JWT). */
export function isAxiosUnauthorized(err: unknown): boolean {
  const ax = err as AxiosError;
  return ax.response?.status === 401;
}

export function getPatientReportPdfUrl(patientId: string, token?: string): string {
  const encoded = encodeURIComponent(patientId);
  return `${baseURL}/api/patient_report_pdf?patient_id=${encoded}&token=${token || ""}`;
}


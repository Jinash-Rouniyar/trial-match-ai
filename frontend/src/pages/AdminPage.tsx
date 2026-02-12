import React, { useEffect, useState } from "react";
import { listPatients, PatientSummary, runBatchMatching, uploadTrials } from "../api/client";

const AdminPage: React.FC = () => {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<string | null>(null);
  const [trialsFile, setTrialsFile] = useState<File | null>(null);
  const [trialsUploading, setTrialsUploading] = useState(false);
  const [trialsMessage, setTrialsMessage] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listPatients();
      setPatients(data.patients);
    } catch {
      setError("Failed to load patients");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const handleRunBatchMatching = async () => {
    if (!patients || patients.length === 0) {
      setBatchStatus("No patients available to match.");
      return;
    }
    try {
      setBatchStatus("Running matching for all patients…");
      const ids = patients.map((p) => p.patient_id);
      const res = await runBatchMatching(ids, "demo");
      const succeeded = res.results.filter((r) => !r.error).length;
      const failed = res.results.filter((r) => r.error).length;
      setBatchStatus(`Completed batch matching. Succeeded: ${succeeded}, Failed: ${failed}.`);
    } catch {
      setBatchStatus("Batch matching failed. Please try again.");
    }
  };

  const handleTrialsFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setTrialsFile(f);
  };

  const handleTrialsUpload = async () => {
    if (!trialsFile) {
      setTrialsMessage("Choose a JSON file with trials.");
      return;
    }
    try {
      setTrialsUploading(true);
      setTrialsMessage(null);
      const text = await trialsFile.text();
      const parsed = JSON.parse(text);
      const trials = Array.isArray(parsed) ? parsed : parsed.trials;
      if (!Array.isArray(trials)) {
        throw new Error("Invalid trials JSON structure.");
      }
      const adminToken =
        window.prompt("Enter admin token (APP_ADMIN_SECRET) for trials upload") || undefined;
      const res = await uploadTrials(trials, adminToken);
      setTrialsMessage(`Uploaded/updated ${res.upserted} trials.`);
    } catch {
      setTrialsMessage("Failed to upload trials JSON. Ensure it is valid.");
    } finally {
      setTrialsUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <div>
          <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">Admin</p>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
            Trials and cohort operations
          </h1>
          <p className="mt-1 text-xs text-slate-600">
            Upload or replace trial datasets and run matching across the current synthetic cohort.
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">
              Cohort overview
            </p>
            <h2 className="mt-1 text-sm font-medium text-slate-900">Current patients</h2>
          </div>
          {patients && patients.length > 0 && (
            <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-[0.7rem] text-slate-700">
              {patients.length} patients
            </span>
          )}
        </div>

        {patients && patients.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleRunBatchMatching}
              className="inline-flex items-center rounded-full bg-slate-900 px-4 py-1.5 text-[0.7rem] font-medium text-white hover:bg-black"
            >
              Run matching for all
            </button>
            {batchStatus && <p className="text-[0.7rem] text-slate-500">{batchStatus}</p>}
          </div>
        )}

        {!loading && patients && patients.length === 0 && (
          <p className="mt-4 text-xs text-slate-500">
            No patients yet. Once users upload patients, they’ll appear here.
          </p>
        )}
      </section>

      <section className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-5 shadow-[0_1px_3px_rgba(15,23,42,0.04)]">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">Trials</p>
            <h2 className="mt-1 text-sm font-medium text-slate-900">Upload trials dataset</h2>
            <p className="mt-1 text-xs text-slate-600">
              JSON array of trials with fields: <code>nct_id</code>, <code>brief_title</code>,{" "}
              <code>criteria</code>, and optional <code>overall_status</code>. Protected by a simple
              admin token.
            </p>
          </div>
        </div>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
          <input
            type="file"
            accept="application/json"
            onChange={handleTrialsFileChange}
            className="block w-full text-xs text-slate-700 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white hover:file:bg-black"
          />
          <button
            type="button"
            onClick={handleTrialsUpload}
            disabled={trialsUploading}
            className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
          >
            {trialsUploading ? "Uploading…" : "Upload trials"}
          </button>
        </div>
        {trialsMessage && <p className="mt-2 text-[0.7rem] text-slate-600">{trialsMessage}</p>}
      </section>
    </div>
  );
};

export default AdminPage;


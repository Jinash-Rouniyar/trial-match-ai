import React, { useEffect, useRef, useState } from "react";
import {
  getApiErrorMessage,
  isAxiosUnauthorized,
  listPatients,
  PatientSummary,
  runBatchMatching,
  uploadTrials,
} from "../api/client";
import { useAuth } from "../hooks/useAuth";

const AdminPage: React.FC = () => {
  const { session, loading: authLoading } = useAuth();
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<string | null>(null);
  const [trialsFiles, setTrialsFiles] = useState<File[]>([]);
  const [trialsUploading, setTrialsUploading] = useState(false);
  const [trialsMessage, setTrialsMessage] = useState<string | null>(null);
  const trialsFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (authLoading || !session?.access_token) {
      return;
    }

    const ac = new AbortController();

    (async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await listPatients({ signal: ac.signal });
        setPatients(data.patients);
      } catch (err) {
        if (ac.signal.aborted) {
          return;
        }
        if (isAxiosUnauthorized(err)) {
          setPatients([]);
          setError(null);
          return;
        }
        setError(getApiErrorMessage(err, "Could not load the patient list."));
      } finally {
        if (!ac.signal.aborted) {
          setLoading(false);
        }
      }
    })();

    return () => ac.abort();
  }, [authLoading, session?.access_token]);

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
    const list = e.target.files;
    setTrialsFiles(list ? Array.from(list) : []);
  };

  const handleTrialsUpload = async () => {
    if (trialsFiles.length === 0) {
      setTrialsMessage("Choose one or more JSON files with trials.");
      return;
    }
    try {
      setTrialsUploading(true);
      setTrialsMessage(null);
      let totalUpserted = 0;
      let totalSkipped = 0;
      const fileErrors: string[] = [];

      for (const file of trialsFiles) {
        try {
          let text = await file.text();
          if (text.charCodeAt(0) === 0xfeff) {
            text = text.slice(1);
          }
          const parsed = JSON.parse(text) as unknown;
          const res = await uploadTrials(parsed);
          totalUpserted += res.upserted;
          totalSkipped += res.skipped ?? 0;
        } catch (err) {
          if (err instanceof SyntaxError) {
            fileErrors.push(`${file.name}: not valid JSON.`);
          } else {
            fileErrors.push(
              `${file.name}: ${getApiErrorMessage(err, "upload failed.")}`
            );
          }
        }
      }

      const parts: string[] = [];
      if (totalUpserted > 0 || totalSkipped > 0) {
        parts.push(
          totalSkipped > 0
            ? `Uploaded/updated ${totalUpserted} trials (${totalSkipped} skipped — missing NCT id or eligibility text).`
            : `Uploaded/updated ${totalUpserted} trials.`
        );
      }
      if (fileErrors.length > 0) {
        parts.push(fileErrors.join(" "));
      }
      setTrialsMessage(parts.join(" ") || "No trials were imported.");

      if (fileErrors.length === 0 && trialsFileInputRef.current) {
        trialsFileInputRef.current.value = "";
        setTrialsFiles([]);
      }
    } catch (err) {
      setTrialsMessage(
        getApiErrorMessage(err, "Failed to upload trials. Check JSON and admin sign-in.")
      );
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
        {error && (
          <p className="mt-2 text-[0.7rem] text-rose-500">{error}</p>
        )}
      </section>

      <section className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-5 shadow-[0_1px_3px_rgba(15,23,42,0.04)]">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">Trials</p>
            <h2 className="mt-1 text-sm font-medium text-slate-900">Upload trials dataset</h2>
            <p className="mt-1 text-xs text-slate-500">
              Upload clinical trials data from{" "}
              <a
                href="https://clinicaltrials.gov/"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-slate-800 underline underline-offset-2 hover:text-slate-950"
              >
                ClinicalTrials.gov
              </a>
              .
            </p>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <input
            ref={trialsFileInputRef}
            type="file"
            accept="application/json,.json"
            multiple
            onChange={handleTrialsFileChange}
            className="block min-w-0 flex-1 cursor-pointer text-xs text-slate-700 file:mr-3 file:cursor-pointer file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white hover:file:bg-black"
          />
          <button
            type="button"
            onClick={handleTrialsUpload}
            disabled={trialsUploading}
            className="shrink-0 cursor-pointer inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {trialsUploading ? "Uploading…" : "Upload trials"}
          </button>
        </div>
        {trialsFiles.length > 0 && (
          <p className="mt-2 text-[0.65rem] text-slate-500">
            {trialsFiles.length} file{trialsFiles.length === 1 ? "" : "s"} selected
            {trialsFiles.length <= 3
              ? `: ${trialsFiles.map((f) => f.name).join(", ")}`
              : ""}
          </p>
        )}
        {trialsMessage && <p className="mt-2 text-[0.7rem] text-slate-600">{trialsMessage}</p>}
      </section>
    </div>
  );
};

export default AdminPage;


import axios from "axios";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchPatientDetail,
  getApiErrorMessage,
  listPatients,
  PatientSummary,
} from "../api/client";
import UploadPanel from "../components/UploadPanel";
import { useAuth } from "../hooks/useAuth";

type PreviewSnapshot = {
  patient_id: string;
  topTrials: { nct_id: string; title: string; score: number }[];
  matchMode?: string;
  matchCreatedAt?: string;
};

const MAX_TRIALS_PREVIEW = 3;

const DashboardPage: React.FC = () => {
  const { user, session, loading: authLoading } = useAuth();
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewSnapshot, setPreviewSnapshot] = useState<PreviewSnapshot | null>(null);
  const navigate = useNavigate();

  const refreshPatientList = async () => {
    if (authLoading || !session?.access_token) {
      return;
    }
    try {
      setListLoading(true);
      const data = await listPatients();
      setPatients(data.patients);
    } catch {
      setPatients([]);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    void refreshPatientList();
  }, [authLoading, session?.access_token]);

  const latestPatientId = patients[0]?.patient_id;

  useEffect(() => {
    if (!latestPatientId) {
      setPreviewSnapshot(null);
      setPreviewError(null);
      setPreviewLoading(false);
      return;
    }

    const ac = new AbortController();

    (async () => {
      try {
        setPreviewLoading(true);
        setPreviewError(null);
        const data = await fetchPatientDetail(latestPatientId, { signal: ac.signal });
        if (ac.signal.aborted) {
          return;
        }
        const latest = data.latest_matches;
        const trials = (latest?.trials || [])
          .slice()
          .sort((a, b) => b.score - a.score)
          .slice(0, MAX_TRIALS_PREVIEW)
          .map((t) => ({
            nct_id: t.nct_id,
            title: t.title,
            score: t.score,
          }));

        setPreviewSnapshot({
          patient_id: data.patient_id,
          topTrials: trials,
          matchMode: latest?.mode,
          matchCreatedAt: latest?.created_at,
        });
      } catch (err) {
        if (ac.signal.aborted || (axios.isAxiosError(err) && err.code === "ERR_CANCELED")) {
          return;
        }
        setPreviewSnapshot(null);
        setPreviewError(getApiErrorMessage(err, "Could not load preview."));
      } finally {
        if (!ac.signal.aborted) {
          setPreviewLoading(false);
        }
      }
    })();

    return () => ac.abort();
  }, [latestPatientId]);

  const goToLatestReport = () => {
    if (!latestPatientId) {
      return;
    }
    navigate(`/patients/${encodeURIComponent(latestPatientId)}/report`);
  };

  const goToLatestPatient = () => {
    if (!latestPatientId) {
      return;
    }
    navigate(`/patients/${encodeURIComponent(latestPatientId)}`);
  };

  const previewBadge = () => {
    if (listLoading && patients.length === 0) {
      return { label: "Loading…", dotClass: "bg-slate-400" };
    }
    if (!patients.length) {
      return { label: "No patients", dotClass: "bg-slate-300" };
    }
    if (previewLoading) {
      return { label: "Loading preview…", dotClass: "bg-amber-400" };
    }
    if (previewError) {
      return { label: "Preview error", dotClass: "bg-rose-400" };
    }
    return { label: "Cohort data", dotClass: "bg-emerald-500" };
  };

  const badge = previewBadge();

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="grid gap-10 md:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] items-center">
        <div className="space-y-4">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
            TrialMatch AI for clinical screening
          </h1>
          <p className="text-sm text-slate-500">
            Upload synthetic patient records, parse eligibility criteria, and review ranked trial
            matches in minutes instead of hours.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="cursor-pointer rounded-full bg-slate-900 px-4 py-2 text-xs font-medium text-white shadow-sm hover:bg-black"
              onClick={() => {
                const el = document.getElementById("upload-card");
                if (el) {
                  el.scrollIntoView({ behavior: "smooth", block: "start" });
                }
              }}
            >
              Upload patient JSON
            </button>
            <button
              type="button"
              className="cursor-pointer rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-900 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!patients.length}
              onClick={goToLatestReport}
            >
              View last matches
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-[0.7rem] text-slate-500">
            <span className="font-medium text-slate-700">Cohort preview</span>
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-[0.65rem] text-slate-600">
              <span className={`h-1.5 w-1.5 rounded-full ${badge.dotClass}`} />
              {badge.label}
            </span>
          </div>
          <div className="mt-3 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-900">Patient cohort</span>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-[0.65rem] text-slate-700">
                {patients.length} patient{patients.length === 1 ? "" : "s"}
              </span>
            </div>

            <div className="mt-2 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-3 py-3 space-y-3">
              {!user && (
                <p className="text-[0.7rem] text-slate-500">Sign in to load cohort data.</p>
              )}
              {user && !patients.length && !listLoading && (
                <p className="text-[0.7rem] text-slate-500">
                  Upload a patient JSON below. This panel will show the latest patient and top
                  trial scores after matching.
                </p>
              )}
              {user && listLoading && !patients.length && (
                <p className="text-[0.7rem] text-slate-500">Loading cohort…</p>
              )}
              {previewError && (
                <p className="text-[0.7rem] text-rose-600">{previewError}</p>
              )}
              {latestPatientId && previewLoading && !previewSnapshot && !previewError && (
                <p className="text-[0.7rem] text-slate-500">Loading latest patient…</p>
              )}
              {previewSnapshot && (
                <div className="space-y-2 text-[0.7rem] text-slate-700">
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-medium text-slate-900">Latest patient</span>
                    <button
                      type="button"
                      onClick={goToLatestPatient}
                      className="shrink-0 cursor-pointer text-[0.65rem] font-medium text-slate-600 underline underline-offset-2 hover:text-slate-900"
                    >
                      Open details
                    </button>
                  </div>
                  <p className="truncate font-mono text-[0.65rem] text-slate-600" title={previewSnapshot.patient_id}>
                    {previewSnapshot.patient_id}
                  </p>
                  <div>
                    <p className="text-[0.65rem] font-medium uppercase tracking-wide text-slate-500">
                      Top trial matches
                    </p>
                    {previewSnapshot.topTrials.length === 0 ? (
                      <p className="mt-0.5 text-slate-500">
                        No runs yet. Open the patient and use &quot;Match to demo trials&quot; or
                        &quot;Match to random trials&quot;.
                      </p>
                    ) : (
                      <ul className="mt-1 space-y-1">
                        {previewSnapshot.topTrials.map((t) => (
                          <li
                            key={t.nct_id}
                            className="flex items-baseline justify-between gap-2 border-b border-slate-100 pb-1 last:border-0 last:pb-0"
                          >
                            <span className="min-w-0 truncate text-slate-800" title={t.title}>
                              <span className="font-mono text-[0.6rem] text-slate-500">{t.nct_id}</span>{" "}
                              {t.title}
                            </span>
                            <span className="shrink-0 font-medium tabular-nums text-slate-900">
                              {Math.round(t.score)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                    {previewSnapshot.matchCreatedAt && previewSnapshot.topTrials.length > 0 && (
                      <p className="mt-2 text-[0.6rem] text-slate-500">
                        Last run: {previewSnapshot.matchCreatedAt}
                        {previewSnapshot.matchMode ? ` · ${previewSnapshot.matchMode}` : ""}
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={goToLatestReport}
                    className="mt-1 cursor-pointer text-[0.65rem] font-medium text-slate-600 underline underline-offset-2 hover:text-slate-900"
                  >
                    Full match report →
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Upload card */}
      <section
        id="upload-card"
        className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3 shadow-[0_1px_3px_rgba(15,23,42,0.08)]"
      >
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">
              PATIENT DATA
            </p>
            <h2 className="mt-1 text-sm font-medium text-slate-900">Upload synthetic patients</h2>
          </div>
        </div>
        <UploadPanel onUploaded={refreshPatientList} />
        {listLoading && <p className="mt-2 text-xs text-slate-500">Loading patients…</p>}
      </section>

      {/* Cohort table */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">
              COHORT OVERVIEW
            </p>
            <h2 className="mt-1 text-sm font-medium text-slate-900">Patient cohort</h2>
          </div>
          {patients.length > 0 && (
            <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-[0.7rem] text-slate-700">
              {patients.length} patient{patients.length === 1 ? "" : "s"}
            </span>
          )}
        </div>

        {!listLoading && !patients.length && (
          <p className="mt-4 text-xs text-slate-500">
            No patients yet. Upload a patient JSON to begin.
          </p>
        )}

        {patients.length > 0 && (
          <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full text-xs">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Patient ID</th>
                  <th className="px-3 py-2 text-left font-medium">Key conditions</th>
                  <th className="hidden px-3 py-2 text-left font-medium sm:table-cell">Created</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <tr key={p.patient_id} className="border-t border-slate-200 align-top">
                    <td className="px-3 py-2 font-medium text-slate-900">{p.patient_id}</td>
                    <td className="px-3 py-2">
                      {(p.conditions || []).length > 0 ? (
                        <span className="inline-flex max-w-[12rem] whitespace-normal break-words rounded-lg bg-slate-100 px-2.5 py-1 text-[0.7rem] leading-snug text-slate-700 sm:max-w-[18rem]">
                          {(p.conditions || []).slice(0, 2).join(", ")}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">None parsed</span>
                      )}
                    </td>
                    <td className="hidden px-3 py-2 text-xs text-slate-500 sm:table-cell">{p.created_at}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        className="inline-flex cursor-pointer items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50"
                        onClick={() =>
                          navigate(`/patients/${encodeURIComponent(p.patient_id)}`)
                        }
                      >
                        View details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;

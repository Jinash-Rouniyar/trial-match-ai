import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listPatients, PatientSummary } from "../api/client";
import UploadPanel from "../components/UploadPanel";

const DashboardPage: React.FC = () => {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

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
              className="rounded-full bg-slate-900 px-4 py-2 text-xs font-medium text-white shadow-sm hover:bg-black"
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
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-900 hover:bg-slate-50"
              disabled={!patients || patients.length === 0}
            >
              View last matches
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between text-[0.7rem] text-slate-500">
            <span>Preview</span>
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Synthetic data
            </span>
          </div>
          <div className="mt-3 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-900">Patient cohort</span>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-[0.65rem] text-slate-700">
                {patients?.length ?? 0} patients
              </span>
            </div>
            <div className="mt-2 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-3 py-3">
              <p className="text-[0.7rem] text-slate-500">
                Upload JSON to see parsed conditions, medications, and match scores here.
              </p>
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
        <UploadPanel onUploaded={refresh} />
        {loading && <p className="mt-2 text-xs text-slate-500">Loading patients…</p>}
        {error && <p className="mt-2 text-xs text-rose-500">{error}</p>}
      </section>

      {/* Cohort table card */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">
              COHORT OVERVIEW
            </p>
            <h2 className="mt-1 text-sm font-medium text-slate-900">Patient cohort</h2>
          </div>
          {patients && patients.length > 0 && (
            <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-[0.7rem] text-slate-700">
              {patients.length} patients
            </span>
          )}
        </div>

        {!loading && patients && patients.length === 0 && (
          <p className="mt-4 text-xs text-slate-500">
            No patients yet. Upload a patient JSON to begin.
          </p>
        )}

        {patients && patients.length > 0 && (
          <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
            <table className="min-w-full text-xs">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Patient ID</th>
                  <th className="px-3 py-2 text-left font-medium">Key conditions</th>
                  <th className="px-3 py-2 text-left font-medium">Created</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <tr key={p.patient_id} className="border-t border-slate-200">
                    <td className="px-3 py-2 font-medium text-slate-900">{p.patient_id}</td>
                    <td className="px-3 py-2">
                      {(p.conditions || []).length > 0 ? (
                        <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-[0.7rem] text-slate-700">
                          {(p.conditions || []).slice(0, 2).join(", ")}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">None parsed</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-500">{p.created_at}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50"
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


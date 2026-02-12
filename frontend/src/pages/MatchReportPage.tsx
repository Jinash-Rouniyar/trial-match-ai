import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchPatientDetail, getPatientReportPdfUrl, MatchDocument } from "../api/client";
import MatchResultTable from "../components/MatchResultTable";

const MatchReportPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchDoc, setMatchDoc] = useState<MatchDocument | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!patientId) return;
      try {
        setLoading(true);
        setError(null);
        const data = await fetchPatientDetail(patientId);
        const latest = (data.latest_matches as MatchDocument | null) ?? null;
        setMatchDoc(latest);
      } catch {
        setError("Failed to load latest match results");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [patientId]);

  if (!patientId) {
    return <p>Missing patient id.</p>;
  }

  return (
    <div className="space-y-6">
      <button
        className="inline-flex items-center text-xs text-slate-500 hover:text-slate-900"
        onClick={() => navigate(-1)}
      >
        ← Back to patient
      </button>
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Match report</h1>
          <p className="mt-1 text-xs text-slate-600">
            Ranked trials for patient {patientId} based on parsed eligibility semantics.
          </p>
        </div>
        <div className="mt-3 flex items-center gap-2 md:mt-0">
          <a
            href={getPatientReportPdfUrl(patientId)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50"
          >
            Download PDF
          </a>
        </div>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 space-y-3 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
        <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">TRIAL MATCHES</p>
        {loading && <p className="text-xs text-slate-600">Loading…</p>}
        {error && <p className="text-xs text-rose-500">{error}</p>}
        {!loading && !matchDoc && (
          <p className="text-xs text-slate-600">
            No match results available yet. Run matching from the patient page.
          </p>
        )}
        {matchDoc && (
          <>
            <p className="text-xs text-slate-600">
              Mode: <span className="font-medium text-slate-900">{matchDoc.mode}</span> · Generated
              at {matchDoc.created_at}
            </p>
            <MatchResultTable trials={matchDoc.trials} />
          </>
        )}
      </div>
    </div>
  );
};

export default MatchReportPage;


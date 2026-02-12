import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchPatientDetail, runMatching, MatchDocument } from "../api/client";

const PatientDetailPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<any | null>(null);
  const [latestMatches, setLatestMatches] = useState<MatchDocument | null>(null);
  const [runningMatch, setRunningMatch] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (!patientId) return;
      try {
        setLoading(true);
        setError(null);
        const data = await fetchPatientDetail(patientId);
        setProfile(data.profile);
        setLatestMatches((data.latest_matches as MatchDocument | null) ?? null);
      } catch (e) {
        setError("Failed to load patient details");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [patientId]);

  const handleRunMatching = async (mode: "demo" | "random") => {
    if (!patientId) return;
    try {
      setRunningMatch(true);
      const doc = await runMatching(patientId, mode);
      setLatestMatches(doc);
      navigate(`/patients/${encodeURIComponent(patientId)}/report`);
    } catch (e) {
      setError("Failed to run matching");
    } finally {
      setRunningMatch(false);
    }
  };

  if (!patientId) {
    return <p>Missing patient id.</p>;
  }

  return (
    <div className="space-y-6">
      <button
        className="inline-flex items-center text-xs text-slate-500 hover:text-slate-900"
        onClick={() => navigate(-1)}
      >
        ← Back to dashboard
      </button>

      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Patient {patientId}</h1>
          <p className="mt-1 text-xs text-slate-500">
            Parsed profile from synthetic EHR – conditions, medications, and clinical narrative.
          </p>
        </div>
      </div>

      {loading && <p className="text-xs text-slate-500">Loading…</p>}
      {error && <p className="text-xs text-rose-500">{error}</p>}

      {profile && (
        <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 space-y-4 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
          <section>
            <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">PROFILE</p>
            <h2 className="mt-1 text-sm font-medium text-slate-900">Clinical summary</h2>
          </section>
          <section>
            <h3 className="text-xs font-medium text-slate-900">Conditions</h3>
            <p className="mt-1 text-xs text-slate-600">
              {profile.conditions && profile.conditions.length
                ? profile.conditions.join(", ")
                : "None parsed"}
            </p>
          </section>
          <section>
            <h3 className="text-xs font-medium text-slate-900">Medications</h3>
            <p className="mt-1 text-xs text-slate-600">
              {profile.medications && profile.medications.length
                ? profile.medications.join(", ")
                : "None parsed"}
            </p>
          </section>
          <section>
            <h3 className="text-xs font-medium text-slate-900">Summary narrative</h3>
            <p className="mt-1 text-xs text-slate-700">
              {profile.text_summary || (
                <span className="text-slate-400">No summary available.</span>
              )}
            </p>
          </section>
          <section>
            <h3 className="text-xs font-medium text-slate-900">Extracted clinical entities</h3>
            <p className="mt-1 text-xs text-slate-600">
              {profile.ner_entities && profile.ner_entities.length
                ? profile.ner_entities.join(", ")
                : "None detected"}
            </p>
          </section>
        </div>
      )}

      <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 space-y-3 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
        <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">
          MATCHING ENGINE
        </p>
        <h2 className="text-sm font-medium text-slate-900">Run trial matching</h2>
        <p className="text-xs text-slate-600">
          Screen this patient against demo or randomly sampled recruiting trials. The first run may
          take a bit longer while models warm up.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            disabled={runningMatch}
            onClick={() => handleRunMatching("demo")}
            className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
          >
            {runningMatch ? "Running…" : "Match to demo trials"}
          </button>
          <button
            disabled={runningMatch}
            onClick={() => handleRunMatching("random")}
            className="inline-flex items-center rounded-full bg-slate-900 px-3 py-1.5 text-[0.7rem] font-medium text-white hover:bg-black disabled:opacity-60"
          >
            {runningMatch ? "Running…" : "Match to random trials"}
          </button>
        </div>
      </div>

      {latestMatches && (
        <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 space-y-2 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
          <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">
            LATEST RUN
          </p>
          <h2 className="mt-1 text-sm font-medium text-slate-900">Latest match results</h2>
          <p className="text-xs text-slate-600">
            Mode: <span className="font-medium text-slate-900">{latestMatches.mode}</span> ·
            Generated at {latestMatches.created_at}
          </p>
          <button
            className="mt-2 inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50"
            onClick={() => navigate(`/patients/${encodeURIComponent(patientId)}/report`)}
          >
            View full report
          </button>
        </div>
      )}
    </div>
  );
};

export default PatientDetailPage;


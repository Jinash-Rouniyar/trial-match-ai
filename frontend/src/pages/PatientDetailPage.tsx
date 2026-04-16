import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchPatientDetail, runMatching, MatchDocument } from "../api/client";

const PatientDetailPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<{
    conditions?: string[];
    medications?: string[];
    text_summary?: string;
    ner_entities?: string[];
  } | null>(null);
  const [latestMatches, setLatestMatches] = useState<MatchDocument | null>(null);
  const [runningMatch, setRunningMatch] = useState(false);
  const [showAllConditions, setShowAllConditions] = useState(false);
  const [showAllMedications, setShowAllMedications] = useState(false);
  const [showFullNarrative, setShowFullNarrative] = useState(false);
  const latestMatchMode = latestMatches?.mode === "demo" ? "All" : latestMatches?.mode;

  const toUniqueList = (items?: string[]) => {
    const out: string[] = [];
    const seen = new Set<string>();
    for (const raw of items || []) {
      const v = (raw || "").trim();
      if (!v) continue;
      const key = v.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(v);
    }
    return out;
  };

  useEffect(() => {
    const load = async () => {
      if (!patientId) return;
      try {
        setLoading(true);
        setError(null);
        const data = await fetchPatientDetail(patientId);
        setProfile(data.profile);
        setLatestMatches((data.latest_matches as MatchDocument | null) ?? null);
      } catch {
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
    } catch {
      setError("Failed to run matching");
    } finally {
      setRunningMatch(false);
    }
  };

  if (!patientId) {
    return <p>Missing patient id.</p>;
  }

  const conditions = toUniqueList(profile?.conditions);
  const medications = toUniqueList(profile?.medications);
  const narrative = (profile?.text_summary || "").trim();

  const conditionsPreview = showAllConditions ? conditions : conditions.slice(0, 12);
  const medicationsPreview = showAllMedications ? medications : medications.slice(0, 10);
  const narrativeSentences = narrative
    ? narrative
        .split(". ")
        .map((s) => s.trim())
        .filter(Boolean)
    : [];
  const narrativePreview = showFullNarrative
    ? narrative
    : `${narrativeSentences.slice(0, 5).join(". ")}${
        narrativeSentences.length > 5 ? "." : ""
      }`;

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
            {!conditions.length ? (
              <p className="mt-1 text-xs text-slate-400">None parsed</p>
            ) : (
              <>
                <p className="mt-1 text-[0.7rem] text-slate-500">
                  {conditions.length} unique conditions
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {conditionsPreview.map((item) => (
                    <span
                      key={item}
                      className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-[0.68rem] text-slate-700"
                    >
                      {item}
                    </span>
                  ))}
                </div>
                {conditions.length > 12 && (
                  <button
                    type="button"
                    onClick={() => setShowAllConditions((v) => !v)}
                    className="mt-2 text-[0.7rem] font-medium text-slate-600 underline underline-offset-2 hover:text-slate-900"
                  >
                    {showAllConditions
                      ? "Show fewer conditions"
                      : `Show all conditions (+${conditions.length - 12})`}
                  </button>
                )}
              </>
            )}
          </section>
          <section>
            <h3 className="text-xs font-medium text-slate-900">Medications</h3>
            {!medications.length ? (
              <p className="mt-1 text-xs text-slate-400">None parsed</p>
            ) : (
              <>
                <p className="mt-1 text-[0.7rem] text-slate-500">
                  {medications.length} unique medications
                </p>
                <ul className="mt-2 space-y-1">
                  {medicationsPreview.map((item) => (
                    <li key={item} className="text-xs text-slate-600">
                      • {item}
                    </li>
                  ))}
                </ul>
                {medications.length > 10 && (
                  <button
                    type="button"
                    onClick={() => setShowAllMedications((v) => !v)}
                    className="mt-2 text-[0.7rem] font-medium text-slate-600 underline underline-offset-2 hover:text-slate-900"
                  >
                    {showAllMedications
                      ? "Show fewer medications"
                      : `Show all medications (+${medications.length - 10})`}
                  </button>
                )}
              </>
            )}
          </section>
          <section>
            <h3 className="text-xs font-medium text-slate-900">Summary narrative</h3>
            {!narrative ? (
              <p className="mt-1 text-xs text-slate-400">No summary available.</p>
            ) : (
              <>
                <p className="mt-1 text-xs leading-5 text-slate-700">{narrativePreview}</p>
                {narrativeSentences.length > 5 && (
                  <button
                    type="button"
                    onClick={() => setShowFullNarrative((v) => !v)}
                    className="mt-2 text-[0.7rem] font-medium text-slate-600 underline underline-offset-2 hover:text-slate-900"
                  >
                    {showFullNarrative ? "Show shorter summary" : "Show full summary"}
                  </button>
                )}
              </>
            )}
          </section>
        </div>
      )}

      <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 space-y-3 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
        <p className="text-[0.7rem] uppercase tracking-[0.12em] text-slate-400">
          MATCHING ENGINE
        </p>
        <h2 className="text-sm font-medium text-slate-900">Run trial matching</h2>
        <p className="text-xs text-slate-600">
          Screen this patient against all uploaded trials, or a small random subset for a
          faster response.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            disabled={runningMatch}
            onClick={() => handleRunMatching("demo")}
            className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[0.7rem] font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
          >
            {runningMatch ? "Running…" : "Match to all trials"}
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
            Mode: <span className="font-medium text-slate-900">{latestMatchMode}</span> ·
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


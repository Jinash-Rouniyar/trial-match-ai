import React from "react";
import { useNavigate } from "react-router-dom";

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-20">
      {/* Hero */}
      <section className="grid gap-12 md:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] items-center">
        <div className="space-y-6">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
            CLINICAL TRIAL MATCHING
          </p>
          <h1 className="text-5xl font-semibold tracking-tight text-slate-900">
            TrialMatch AI for synthetic cohorts
          </h1>
          <p className="text-base text-slate-600 max-w-xl">
            Upload synthetic EHRs, parse eligibility criteria with LLMs, and review ranked trial
            matches in a clean, clinician-friendly workspace.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => navigate("/login?role=user")}
              className="rounded-full bg-slate-900 px-6 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-black"
            >
              Get started as user
            </button>
            <button
              type="button"
              onClick={() => navigate("/login?role=admin")}
              className="rounded-full border border-slate-200 bg-white px-6 py-2.5 text-sm font-medium text-slate-900 hover:bg-slate-50"
            >
              Admin sign in
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_18px_45px_rgba(15,23,42,0.08)]">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Trial matching preview</span>
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Synthetic data
            </span>
          </div>
          <div className="mt-4 space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-900">1. Upload patients</span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[0.7rem] text-slate-700">
                JSON EHRs
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-900">2. Parse eligibility</span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[0.7rem] text-slate-700">
                Phi-3 + BioLinkBERT
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-900">3. Review matches</span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[0.7rem] text-slate-700">
                Ranked trials
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Feature band */}
      <section className="grid gap-8 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
          <p className="text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">
            LLM PIPELINE
          </p>
          <h2 className="mt-3 text-base font-medium text-slate-900">Eligibility understanding</h2>
          <p className="mt-2 text-sm text-slate-600">
            Phi-3 parses free-text inclusion and exclusion criteria into structured checklists your
            matching engine can reason over.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
          <p className="text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">SEMANTICS</p>
          <h2 className="mt-3 text-base font-medium text-slate-900">Biomedical matching core</h2>
          <p className="mt-2 text-sm text-slate-600">
            BioLinkBERT embeddings capture clinical meaning so that exclusion checks and inclusion
            scores go beyond keyword overlaps.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_1px_3px_rgba(15,23,42,0.08)]">
          <p className="text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">WORKFLOW</p>
          <h2 className="mt-3 text-base font-medium text-slate-900">From JSON to report</h2>
          <p className="mt-2 text-sm text-slate-600">
            Upload Synthea-style EHR JSON, run matching, and export a clinician-friendly PDF report
            for each patient in just a few clicks.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="grid gap-10 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] items-start">
        <div className="space-y-3">
          <p className="text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">
            HOW IT WORKS
          </p>
          <h2 className="text-xl font-semibold text-slate-900">From upload to ranked trials</h2>
          <p className="text-sm text-slate-600">
            TrialMatch AI wraps patient ingestion, eligibility parsing, semantic matching, and
            report generation into a single, focused workflow.
          </p>
          <ul className="mt-3 space-y-1.5 text-sm text-slate-600">
            <li>– Users upload patient JSON and inspect parsed clinical profiles.</li>
            <li>– Matching runs against curated trial datasets managed in the admin view.</li>
            <li>– Clinician-style reports can be downloaded as PDFs for each run.</li>
          </ul>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_1px_3px_rgba(15,23,42,0.08)] text-sm text-slate-600">
          <p className="text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">Workflow</p>
          <ol className="mt-3 space-y-2 list-decimal list-inside">
            <li>Sign in and open the workspace to upload patients.</li>
            <li>Switch to the admin portal to upload or replace trial datasets.</li>
            <li>Run matching and generate reports to review eligibility at a glance.</li>
          </ol>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;


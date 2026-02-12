import React from "react";
import { Routes, Route, Link, NavLink } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import AdminPage from "./pages/AdminPage";
import PatientDetailPage from "./pages/PatientDetailPage";
import MatchReportPage from "./pages/MatchReportPage";

const App: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#FDFCFC] text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-6 h-16">
          <Link
            to="/"
            className="text-base font-semibold tracking-tight text-slate-900 md:text-lg"
          >
            TrialMatch AI
          </Link>
          <nav className="flex items-center gap-3 text-xs">
            <NavLink
              to="/app"
              className={({ isActive }) =>
                `rounded-full px-3 py-1.5 ${
                  isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
                }`
              }
            >
              Workspace
            </NavLink>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `rounded-full px-3 py-1.5 ${
                  isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
                }`
              }
            >
              Admin
            </NavLink>
            <NavLink
              to="/login"
              className={({ isActive }) =>
                `rounded-full border border-slate-200 px-3 py-1.5 ${
                  isActive ? "bg-slate-50 text-slate-900" : "text-slate-600 hover:text-slate-900"
                }`
              }
            >
              Login
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-4 py-10">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<AuthPage />} />
            <Route path="/app" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/patients/:patientId" element={<PatientDetailPage />} />
            <Route path="/patients/:patientId/report" element={<MatchReportPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
};

export default App;


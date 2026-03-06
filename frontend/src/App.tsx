import React, { useRef, useState, useEffect } from "react";
import { Routes, Route, Link, NavLink, useNavigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import AdminPage from "./pages/AdminPage";
import PatientDetailPage from "./pages/PatientDetailPage";
import MatchReportPage from "./pages/MatchReportPage";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import { supabase } from "./api/supabaseClient";

/* ── Avatar + dropdown ─────────────────────────────────────────── */
const ProfileMenu: React.FC<{ email: string | undefined; role: string }> = ({ email, role }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setOpen(false);
    navigate("/login");
  };

  const isAdmin = role === "admin";

  return (
    <div ref={ref} className="relative">
      {/* Avatar button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-bold transition-opacity hover:opacity-80 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 ${isAdmin ? "bg-violet-100 text-violet-700" : "bg-indigo-100 text-indigo-700"
          }`}
        aria-label="Account menu"
      >
        {isAdmin ? "A" : "U"}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 mt-2 w-56 origin-top-right rounded-xl border border-slate-200 bg-white shadow-lg ring-1 ring-black/5 z-50">
          {/* User info */}
          <div className="border-b border-slate-100 px-4 py-3">
            <div className="flex items-center gap-2">
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${isAdmin ? "bg-violet-100 text-violet-700" : "bg-indigo-100 text-indigo-700"
                  }`}
              >
                {isAdmin ? "A" : "U"}
              </div>
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-slate-900">{email}</p>
                <span
                  className={`mt-0.5 inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium ${isAdmin
                    ? "bg-violet-50 text-violet-700"
                    : "bg-indigo-50 text-indigo-600"
                    }`}
                >
                  {isAdmin ? "Admin" : "User"}
                </span>
              </div>
            </div>
          </div>

          {/* Menu items */}
          <div className="py-1">
            {isAdmin && (
              <button
                onClick={() => { navigate("/admin"); setOpen(false); }}
                className="flex w-full items-center gap-2 px-4 py-2 text-left text-xs text-slate-700 hover:bg-slate-50"
              >
                <svg className="h-3.5 w-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Admin Panel
              </button>
            )}
            <button
              onClick={() => { navigate("/app"); setOpen(false); }}
              className="flex w-full items-center gap-2 px-4 py-2 text-left text-xs text-slate-700 hover:bg-slate-50"
            >
              <svg className="h-3.5 w-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              Workspace
            </button>
          </div>

          {/* Logout */}
          <div className="border-t border-slate-100 py-1">
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 px-4 py-2 text-left text-xs text-rose-600 hover:bg-rose-50"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const App: React.FC = () => {
  const { user } = useAuth();
  const role =
    user?.app_metadata?.role ||
    user?.user_metadata?.role ||
    "user";

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
          <nav className="flex items-center text-xs">
            {user ? (
              <ProfileMenu email={user.email} role={role} />
            ) : (
              <NavLink
                to="/login"
                className={({ isActive }) =>
                  `rounded-full border border-slate-200 px-3 py-1.5 ${isActive ? "bg-slate-50 text-slate-900" : "text-slate-600 hover:text-slate-900"}`
                }
              >
                Login
              </NavLink>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-4 py-10">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<AuthPage />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/app" element={<DashboardPage />} />
              <Route path="/patients/:patientId" element={<PatientDetailPage />} />
              <Route path="/patients/:patientId/report" element={<MatchReportPage />} />
            </Route>

            <Route element={<ProtectedRoute requireAdmin={true} />}>
              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Routes>
        </div>
      </main>
    </div>
  );
};

export default App;


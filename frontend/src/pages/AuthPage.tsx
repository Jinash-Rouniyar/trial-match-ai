import React, { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

type Role = "user" | "admin";
type Mode = "login" | "signup";

function useQueryRole(): Role {
  const location = useLocation();
  return useMemo(() => {
    const params = new URLSearchParams(location.search);
    const r = params.get("role");
    return r === "admin" ? "admin" : "user";
  }, [location.search]);
}

const AuthPage: React.FC = () => {
  const navigate = useNavigate();
  const initialRole = useQueryRole();
  const [role, setRole] = useState<Role>(initialRole);
  const [mode, setMode] = useState<Mode>("login");

  const handleSubmit: React.FormEventHandler = (e) => {
    e.preventDefault();
    if (role === "admin") {
      navigate("/admin");
    } else {
      navigate("/app");
    }
  };

  return (
    <div className="flex justify-center">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_18px_45px_rgba(15,23,42,0.08)]">
        <div className="space-y-2 text-center">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-slate-400">Access</p>
          <h1 className="text-xl font-semibold text-slate-900">
            {role === "admin" ? "Admin portal" : "TrialMatch workspace"}
          </h1>
          <p className="text-xs text-slate-600">
            {role === "admin"
              ? "Upload trials and manage cohort-wide matching from the admin surface."
              : "Upload synthetic patients and review trial matches in one place."}
          </p>
        </div>

        <div className="flex gap-2 rounded-full bg-slate-50 p-1 text-[0.7rem]">
          <button
            type="button"
            onClick={() => setRole("user")}
            className={`flex-1 rounded-full px-3 py-1.5 font-medium ${
              role === "user"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            User
          </button>
          <button
            type="button"
            onClick={() => setRole("admin")}
            className={`flex-1 rounded-full px-3 py-1.5 font-medium ${
              role === "admin"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Admin
          </button>
        </div>

        <div className="flex gap-2 rounded-full bg-slate-50 p-1 text-[0.7rem]">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`flex-1 rounded-full px-3 py-1.5 font-medium ${
              mode === "login"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Log in
          </button>
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={`flex-1 rounded-full px-3 py-1.5 font-medium ${
              mode === "signup"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Sign up
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2 text-left text-xs">
            <div>
              <label className="block text-slate-600 mb-1">Email</label>
              <input
                type="email"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 outline-none focus:border-slate-400 focus:bg-white"
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="block text-slate-600 mb-1">
                {mode === "signup" ? "Create password" : "Password"}
              </label>
              <input
                type="password"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 outline-none focus:border-slate-400 focus:bg-white"
                placeholder="••••••••"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            className="inline-flex w-full items-center justify-center rounded-full bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-black"
          >
            {mode === "signup"
              ? role === "admin"
                ? "Create admin account"
                : "Create workspace account"
              : role === "admin"
              ? "Enter admin portal"
              : "Enter workspace"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;


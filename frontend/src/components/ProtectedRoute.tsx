import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

interface ProtectedRouteProps {
    requireAdmin?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requireAdmin = false }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="p-10 text-center text-sm text-slate-500">Loading authentication...</div>;
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (requireAdmin && user.app_metadata?.role !== "admin" && user.user_metadata?.role !== "admin") {
        // If admin is required but user is not admin, push them to app
        return <Navigate to="/app" replace />;
    }

    return <Outlet />;
};

export default ProtectedRoute;

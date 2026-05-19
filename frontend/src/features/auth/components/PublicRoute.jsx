import { Navigate } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";

const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--page-bg)]">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
      </div>
    );
  }

  if (isAuthenticated) {
    if (user?.is_admin) {
      return <Navigate to="/admin/dashboard" replace />;
    }

    return <Navigate to={user?.is_onboarding_completed ? "/scenarios" : "/onboarding"} replace />;
  }

  return children;
};

export default PublicRoute;

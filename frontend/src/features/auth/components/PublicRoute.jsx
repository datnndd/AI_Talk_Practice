import { Navigate } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";

const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-50">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to={user?.is_admin ? "/admin/scenarios" : "/dashboard"} replace />;
  }

  return children;
};

export default PublicRoute;

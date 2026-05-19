import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";

const PrivateRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--page-bg)]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!user?.is_admin && !user?.is_onboarding_completed && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  if (requireAdmin && !user?.is_admin) {
    return <Navigate to="/scenarios" replace />;
  }

  return children;
};

export default PrivateRoute;

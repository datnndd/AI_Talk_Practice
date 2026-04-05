import { Navigate } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";

const PrivateRoute = ({ children, requireAdmin = false, requireSubscription = false }) => {
  const { isAuthenticated, isLoading, user, isSubscribed } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  if (requireSubscription && !user?.is_admin && !isSubscribed) {
    return <Navigate to="/subscription" replace />;
  }

  return children;
};

export default PrivateRoute;

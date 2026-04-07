import { Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import { AppLayout } from "@/app/layouts";
import PrivateRoute from "@/features/auth/components/PrivateRoute";
import PublicRoute from "@/features/auth/components/PublicRoute";

const LandingPage = lazy(() => import("@/features/landing/pages/LandingPage"));
const LoginPage = lazy(() => import("@/features/auth/pages/LoginPage"));
const RegisterPage = lazy(() => import("@/features/auth/pages/RegisterPage"));
const OnboardingPage = lazy(() => import("@/features/onboarding/pages/OnboardingPage"));
const PracticeTopicPage = lazy(() => import("@/features/practice/pages/PracticeTopicPage"));
const PracticeSessionPage = lazy(() => import("@/features/practice/pages/PracticeSessionPage"));
const ProfileSettingsPage = lazy(() => import("@/features/profile/pages/ProfileSettingsPage"));
const DashboardPage = lazy(() => import("@/features/dashboard/pages/DashboardPage"));
const AdminUsersPage = lazy(() => import("@/features/admin-users/pages/AdminUsersPage"));
const AdminScenariosPage = lazy(() => import("@/features/admin-scenarios/pages/AdminScenariosPage"));
const AdminPaymentsPage = lazy(() => import("@/features/admin-payments/pages/AdminPaymentsPage"));
const SubscriptionPage = lazy(() => import("@/features/subscription/pages/SubscriptionPage"));

const RouteFallback = () => (
  <div className="flex min-h-[100dvh] items-center justify-center bg-zinc-50">
    <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
  </div>
);

const withSuspense = (element) => (
  <Suspense fallback={<RouteFallback />}>
    {element}
  </Suspense>
);

const withAppLayout = (element, options = {}) => withSuspense(<AppLayout {...options}>{element}</AppLayout>);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={withSuspense(<LandingPage />)} />
        <Route path="/login" element={<PublicRoute>{withSuspense(<LoginPage />)}</PublicRoute>} />
        <Route path="/register" element={<PublicRoute>{withSuspense(<RegisterPage />)}</PublicRoute>} />
        
        {/* Protected Routes */}
        <Route path="/onboarding" element={<PrivateRoute>{withSuspense(<OnboardingPage />)}</PrivateRoute>} />
        <Route path="/topics" element={<PrivateRoute>{withAppLayout(<PracticeTopicPage />)}</PrivateRoute>} />
        <Route path="/practice/:id" element={<PrivateRoute requireSubscription>{withSuspense(<PracticeSessionPage />)}</PrivateRoute>} />
        <Route path="/profile" element={<PrivateRoute>{withAppLayout(<ProfileSettingsPage />)}</PrivateRoute>} />
        <Route path="/dashboard" element={<PrivateRoute>{withAppLayout(<DashboardPage />)}</PrivateRoute>} />
        <Route path="/subscription" element={<PrivateRoute>{withAppLayout(<SubscriptionPage />)}</PrivateRoute>} />
        
        {/* Admin Routes */}
        <Route path="/admin/users" element={<PrivateRoute requireAdmin>{withSuspense(<AdminUsersPage />)}</PrivateRoute>} />
        <Route path="/admin/scenarios" element={<PrivateRoute requireAdmin>{withSuspense(<AdminScenariosPage />)}</PrivateRoute>} />
        <Route path="/admin/payments" element={<PrivateRoute requireAdmin>{withSuspense(<AdminPaymentsPage />)}</PrivateRoute>} />
      </Routes>
    </Router>
  );
}

export default App;

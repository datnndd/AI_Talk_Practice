import { Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import PrivateRoute from "@/features/auth/components/PrivateRoute";

const LandingPage = lazy(() => import("@/features/landing/pages/LandingPage"));
const LoginPage = lazy(() => import("@/features/auth/pages/LoginPage"));
const RegisterPage = lazy(() => import("@/features/auth/pages/RegisterPage"));
const OnboardingPage = lazy(() => import("@/features/onboarding/pages/OnboardingPage"));
const PracticeTopicPage = lazy(() => import("@/features/practice/pages/PracticeTopicPage"));
const PracticeSessionPage = lazy(() => import("@/features/practice/pages/PracticeSessionPage"));
const ProfileSettingsPage = lazy(() => import("@/features/profile/pages/ProfileSettingsPage"));
const DashboardPage = lazy(() => import("@/features/dashboard/pages/DashboardPage"));
const AdminScenariosPage = lazy(() => import("@/features/admin-scenarios/pages/AdminScenariosPage"));

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

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={withSuspense(<LandingPage />)} />
        <Route path="/login" element={withSuspense(<LoginPage />)} />
        <Route path="/register" element={withSuspense(<RegisterPage />)} />
        
        {/* Protected Routes */}
        <Route path="/onboarding" element={<PrivateRoute>{withSuspense(<OnboardingPage />)}</PrivateRoute>} />
        <Route path="/topics" element={<PrivateRoute>{withSuspense(<PracticeTopicPage />)}</PrivateRoute>} />
        <Route path="/practice/:id" element={<PrivateRoute>{withSuspense(<PracticeSessionPage />)}</PrivateRoute>} />
        <Route path="/profile" element={<PrivateRoute>{withSuspense(<ProfileSettingsPage />)}</PrivateRoute>} />
        <Route path="/dashboard" element={<PrivateRoute>{withSuspense(<DashboardPage />)}</PrivateRoute>} />
        
        {/* Admin Routes */}
        <Route path="/admin/scenarios" element={<PrivateRoute requireAdmin>{withSuspense(<AdminScenariosPage />)}</PrivateRoute>} />
      </Routes>
    </Router>
  );
}

export default App;

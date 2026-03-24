import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import PracticeTopic from "./pages/PracticeTopic";
import PracticeSession from "./pages/PracticeSession";
import ProfileSettings from "./pages/ProfileSettings";
import Dashboard from "./pages/Dashboard";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AdminScenarios from "./pages/AdminScenarios";
import PrivateRoute from "./components/PrivateRoute";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Protected Routes */}
        <Route path="/topics" element={<PrivateRoute><PracticeTopic /></PrivateRoute>} />
        <Route path="/practice/:id" element={<PrivateRoute><PracticeSession /></PrivateRoute>} />
        <Route path="/profile" element={<PrivateRoute><ProfileSettings /></PrivateRoute>} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        
        {/* Admin Routes */}
        <Route path="/admin/scenarios" element={<PrivateRoute><AdminScenarios /></PrivateRoute>} />
      </Routes>
    </Router>
  );
}

export default App;

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import PracticeTopic from "./pages/PracticeTopic";
import PracticeSession from "./pages/PracticeSession";
import ProfileSettings from "./pages/ProfileSettings";
import Dashboard from "./pages/Dashboard";
import LoginPage from "./pages/LoginPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/topics" element={<PracticeTopic />} />
        <Route path="/practice/:id" element={<PracticeSession />} />
        <Route path="/profile" element={<ProfileSettings />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </Router>
  );
}

export default App;

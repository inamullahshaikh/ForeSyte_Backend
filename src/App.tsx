import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import SignupPage from "./pages/SignUpPage";
import LoginPage from "./pages/LoginPage";
import UploadSeatingPlanPage from "./pages/UploadSeatingPlanPage";
import DashboardPage from "./pages/DashboardPage";
import IncidentsPage from "./pages/Incidents";
import LoginSuccess from "./pages/LoginSuccess";
import ProtectedRoute from "./components/ProtectedRoute";
import SelectRole from "./pages/SelectRole";
import StudentDashboardPage from "./student-portal/dashboard";
import MonitoringPage from "./pages/MonitoringPage";
import ReportsPage from "./pages/ReportsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SettingsPage from "./pages/SettingsPage";
import UsersPage from "./pages/UsersPage";
import ExamsPage from "./pages/ExamsPage";
import SeatingPlansPage from "./pages/SeatingPlansPage";

// Investigator Portal Pages
import InvestigatorDashboard from "./investigator-portal/InvestigatorDashboard";
import ViolationsPage from "./investigator-portal/ViolationsPage";
import StudentActivitiesPage from "./investigator-portal/StudentActivitiesPage";
import InvigilatorActivitiesPage from "./investigator-portal/InvigilatorActivitiesPage";
import InvestigatorReportsPage from "./investigator-portal/ReportsPage";
import InvestigatorSettingsPage from "./investigator-portal/SettingsPage";
import VideoProcessingPage from "./investigator-portal/VideoProcessingPage";
import LiveMonitoringPage from "./investigator-portal/LiveMonitoringPage"; 
function App() {
  return (
    <Router>
      <Routes>
        {/* Redirect root to dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        {/* Main Routes */}
        <Route path="/select-role" element={<SelectRole />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/upload-seating-plan"
          element={
            <ProtectedRoute>
              <UploadSeatingPlanPage />
            </ProtectedRoute>
          }
        />
        <Route 
          path="/incidents" 
          element={
            <ProtectedRoute>
              <IncidentsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/monitoring" 
          element={
            <ProtectedRoute>
              <MonitoringPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/reports" 
          element={
            <ProtectedRoute>
              <ReportsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/analytics" 
          element={
            <ProtectedRoute>
              <AnalyticsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/settings" 
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/users" 
          element={
            <ProtectedRoute>
              <UsersPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/exams" 
          element={
            <ProtectedRoute>
              <ExamsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/seating-plans" 
          element={
            <ProtectedRoute>
              <SeatingPlansPage />
            </ProtectedRoute>
          } 
        />
        {/* Google Login redirect handler */}
        <Route path="/login-success" element={<LoginSuccess />} />
        <Route 
          path="/student/dashboard" 
          element={
            <ProtectedRoute>
              <StudentDashboardPage />
            </ProtectedRoute>
          } 
        />

        {/* Investigator Portal Routes */}
        <Route 
          path="/investigator/dashboard" 
          element={
            <ProtectedRoute>
              <InvestigatorDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/investigator/violations" 
          element={
            <ProtectedRoute>
              <ViolationsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/investigator/student-activities" 
          element={
            <ProtectedRoute>
              <StudentActivitiesPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/investigator/invigilator-activities" 
          element={
            <ProtectedRoute>
              <InvigilatorActivitiesPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/investigator/video-processing" 
          element={
            <ProtectedRoute>
              <VideoProcessingPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/investigator/live-monitoring" 
          element={
            <ProtectedRoute>
              <LiveMonitoringPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/investigator/reports" 
          element={
            <ProtectedRoute>
              <InvestigatorReportsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/investigator/settings" 
          element={
            <ProtectedRoute>
              <InvestigatorSettingsPage />
            </ProtectedRoute>
          } 
        />

      </Routes>
    </Router>
  );
}

export default App;

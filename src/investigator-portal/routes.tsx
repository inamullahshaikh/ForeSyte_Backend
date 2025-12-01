import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";
import InvestigatorDashboard from "./InvestigatorDashboard";
import ViolationsPage from "./ViolationsPage";
import StudentActivitiesPage from "./StudentActivitiesPage";
import InvigilatorActivitiesPage from "./InvigilatorActivitiesPage";
import VideoProcessingPage from "./VideoProcessingPage";
import LiveMonitoringPage from "./LiveMonitoringPage";
import ReportsPage from "./ReportsPage";
import SettingsPage from "./SettingsPage";

const InvestigatorRoutes = () => {
  return (
    <Routes>
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <InvestigatorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/violations"
        element={
          <ProtectedRoute>
            <ViolationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student-activities"
        element={
          <ProtectedRoute>
            <StudentActivitiesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/invigilator-activities"
        element={
          <ProtectedRoute>
            <InvigilatorActivitiesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/video-processing"
        element={
          <ProtectedRoute>
            <VideoProcessingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/live-monitoring"
        element={
          <ProtectedRoute>
            <LiveMonitoringPage />
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
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/investigator/dashboard" replace />} />
    </Routes>
  );
};

export default InvestigatorRoutes;


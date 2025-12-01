import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

// ✅ Student Pages
import StudentLoginPage from "../pages/LoginPage";
import StudentDashboardPage from "./dashboard";
import StudentUploadPage from "./uploadImage";
import StudentDisciplinaryRecordsPage from "./dcRecords";
import StudentSettingsPage from "./settings";

// ✅ ProtectedRoute Props Interface
interface ProtectedRouteProps {
  element: React.ReactElement;
}

// ✅ ProtectedRoute Component
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ element }) => {
  const isAuthenticated = (): boolean => {
    return sessionStorage.getItem("token") !== null;
  };

  return isAuthenticated() ? element : <Navigate to="/student-login" replace />;
};

// ✅ Main StudentRoutes Component
const StudentRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Route */}
      <Route path="../pages/login" element={<StudentLoginPage />} />

      {/* Protected Routes */}
      <Route
        path="/student-portal/dashboard"
        element={<ProtectedRoute element={<StudentDashboardPage />} />}
      />
      <Route
        path="/student-portal/uploadImage"
        element={<ProtectedRoute element={<StudentUploadPage />} />}
      />

      
      <Route
        path="/student-portal/dcRecords"
        element={<ProtectedRoute element={<StudentDisciplinaryRecordsPage />} />}
      />
      <Route
        path="/student-portal/settings"
        element={<ProtectedRoute element={<StudentSettingsPage />} />}
      />

      {/* Redirect to Dashboard by default */}
      <Route
        path="/student-portal/*"
        element={<Navigate to="/student-dashboard" replace />}
      />
    </Routes>
  );
};

export default StudentRoutes;

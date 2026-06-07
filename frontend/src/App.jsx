import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider, ROLE_ROUTES, useAuth } from "./contexts/AuthContext";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";

import LoginPage              from "./pages/auth/LoginPage";
import SuperAdminDashboard    from "./pages/superadmin/SuperAdminDashboard";
import DistrictAdminDashboard from "./pages/districtadmin/DistrictAdminDashboard";
import TeacherDashboard       from "./pages/teacher/TeacherDashboard";
import AttendancePage         from "./pages/teacher/AttendancePage";
import SpEdDashboard          from "./pages/sped/SpEdDashboard";
import IepTrackerPage         from "./pages/sped/IepTrackerPage";
import PrincipalDashboard     from "./pages/principal/PrincipalDashboard";
import ParentPortal           from "./pages/parent/ParentPortal";

const ALL_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher", "SpEdCoordinator", "Parent"];

function ComingSoon({ label }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <p className="text-text-secondary text-sm font-medium">{label}</p>
        <p className="text-text-muted text-xs mt-1">Coming in a later step</p>
      </div>
    </div>
  );
}

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={ROLE_ROUTES[user.role] || "/login"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#ffffff",
              color: "#111827",
              border: "1px solid #e4e7ef",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.07)",
              borderRadius: "0.875rem",
              fontSize: "0.875rem",
            },
          }}
        />
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<LoginPage />} />

          {/* SuperAdmin */}
          <Route path="/superadmin" element={
            <ProtectedRoute allowedRoles={["SuperAdmin"]}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route index element={<SuperAdminDashboard />} />
            <Route path="tenants"  element={<ComingSoon label="Tenant Management" />} />
            <Route path="users"    element={<ComingSoon label="User Management" />} />
            <Route path="ai"       element={<ComingSoon label="AI Queries (D7)" />} />
            <Route path="settings" element={<ComingSoon label="Settings" />} />
          </Route>

          {/* DistrictAdmin */}
          <Route path="/districtadmin" element={
            <ProtectedRoute allowedRoles={["DistrictAdmin", "SuperAdmin"]}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route index element={<DistrictAdminDashboard />} />
            <Route path="students" element={<ComingSoon label="Students" />} />
            <Route path="staff"    element={<ComingSoon label="Staff Management" />} />
            <Route path="budget"   element={<ComingSoon label="Budget Module" />} />
            <Route path="reports"  element={<ComingSoon label="Reports" />} />
            <Route path="ai"       element={<ComingSoon label="AI Queries (D7)" />} />
            <Route path="settings" element={<ComingSoon label="Settings" />} />
          </Route>

          {/* Principal */}
          <Route path="/principal" element={
            <ProtectedRoute allowedRoles={ALL_ROLES}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route index element={<PrincipalDashboard />} />
            <Route path="students"   element={<ComingSoon label="Students (D5)" />} />
            <Route path="attendance" element={<ComingSoon label="Attendance (D5)" />} />
            <Route path="scheduling" element={<ComingSoon label="Scheduling (D5)" />} />
            <Route path="reports"    element={<ComingSoon label="Reports (D5)" />} />
            <Route path="ai"         element={<ComingSoon label="AI Queries (D7)" />} />
          </Route>

          {/* Teacher */}
          <Route path="/teacher" element={
            <ProtectedRoute allowedRoles={ALL_ROLES}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route index           element={<TeacherDashboard />} />
            <Route path="attendance" element={<AttendancePage />} />
            <Route path="gradebook"  element={<ComingSoon label="Gradebook (coming next)" />} />
            <Route path="schedule"   element={<ComingSoon label="My Schedule" />} />
            <Route path="messages"   element={<ComingSoon label="Messages" />} />
            <Route path="ai"         element={<ComingSoon label="AI Queries (D7)" />} />
          </Route>

          {/* SpEd */}
          <Route path="/sped" element={
            <ProtectedRoute allowedRoles={ALL_ROLES}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route index element={<SpEdDashboard />} />
            <Route path="iep"        element={<IepTrackerPage />} />
            <Route path="students"   element={<ComingSoon label="SpEd Students" />} />
            <Route path="compliance" element={<ComingSoon label="Compliance" />} />
            <Route path="ai"         element={<ComingSoon label="AI Queries (D7)" />} />
          </Route>

          {/* Parent */}
          <Route path="/parent" element={
            <ProtectedRoute allowedRoles={ALL_ROLES}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route index element={<ParentPortal />} />
            <Route path="grades"     element={<ComingSoon label="Grades (D6)" />} />
            <Route path="attendance" element={<ComingSoon label="Attendance (D6)" />} />
            <Route path="messages"   element={<ComingSoon label="Messages (D6)" />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

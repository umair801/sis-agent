import { Navigate, useLocation } from "react-router-dom";
import { useAuth, ROLE_ROUTES } from "../../contexts/AuthContext";
import { Spinner } from "../ui/Spinner";

export function ProtectedRoute({ allowedRoles, children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-surface">
        <Spinner className="w-8 h-8 border-surface-border border-t-primary-500" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    const home = ROLE_ROUTES[user.role] || "/login";
    return <Navigate to={home} replace />;
  }

  return children;
}

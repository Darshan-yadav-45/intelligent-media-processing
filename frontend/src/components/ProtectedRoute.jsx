import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute() {
  const { user } = useAuth();
  const hasToken = !!localStorage.getItem("access_token");

  if (!user && !hasToken) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

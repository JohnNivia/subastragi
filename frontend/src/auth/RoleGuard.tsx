import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { RoleName } from "../types";

export function RoleGuard({ roles }: { roles: RoleName[] }) {
  const { roles: userRoles } = useAuth();
  return userRoles.some((role) => roles.includes(role)) ? (
    <Outlet />
  ) : (
    <Navigate to="/app" replace />
  );
}

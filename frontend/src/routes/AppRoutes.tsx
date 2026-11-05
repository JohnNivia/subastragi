import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "../auth/ProtectedRoute";
import { RoleGuard } from "../auth/RoleGuard";
import { useAuth } from "../auth/AuthContext";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { AuthLayout } from "../layouts/AuthLayout";
import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";
import Dashboard from "../pages/Dashboard";
import Users from "../pages/admin/Users";
import Breeds from "../pages/ganadero/Breeds";
import Lots from "../pages/ganadero/Lots";
import Auctions from "../pages/comprador/Auctions";
import Bids from "../pages/comprador/Bids";
import Adjudications from "../pages/comprador/Adjudications";
import Profile from "../pages/Profile";

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="screen-state">Cargando SubastAgro...</div>;
  return <Navigate to={user ? "/app" : "/login"} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="profile" element={<Profile />} />
          <Route element={<RoleGuard roles={["ADMINISTRADOR"]} />}>
            <Route path="users" element={<Users />} />
          </Route>
          <Route element={<RoleGuard roles={["ADMINISTRADOR", "GANADERO", "COMPRADOR"]} />}>
            <Route path="breeds" element={<Breeds />} />
            <Route path="auctions" element={<Auctions />} />
          </Route>
          <Route element={<RoleGuard roles={["ADMINISTRADOR", "GANADERO"]} />}>
            <Route path="lots" element={<Lots />} />
          </Route>
          <Route element={<RoleGuard roles={["ADMINISTRADOR", "COMPRADOR"]} />}>
            <Route path="bids" element={<Bids />} />
            <Route path="adjudications" element={<Adjudications />} />
          </Route>
        </Route>
      </Route>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  );
}

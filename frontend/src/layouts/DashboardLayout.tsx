import { useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "../components/layout/Sidebar";
import { Topbar } from "../components/layout/Topbar";
import { useAuth } from "../auth/AuthContext";

export function DashboardLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);
  const { signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate("/login", { replace: true });
    } catch {
      setSignOutError("No se pudo confirmar el cierre en el servidor; la sesión local fue eliminada.");
      navigate("/login", { replace: true });
    }
  };

  return (
    <div className="dashboard-shell">
      <div className={`sidebar-wrap ${menuOpen ? "sidebar-open" : ""}`}>
        <Sidebar onSignOut={handleSignOut} />
      </div>
      {menuOpen && <button className="sidebar-scrim" aria-label="Cerrar navegación" onClick={() => setMenuOpen(false)} />}
      <div className="dashboard-main">
        <Topbar onMenuClick={() => setMenuOpen(true)} />
        <main className="content"><Outlet /></main>
      </div>
      {signOutError && <div className="toast-error">{signOutError}</div>}
    </div>
  );
}

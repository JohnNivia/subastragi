import {
  Activity,
  Beef,
  Gavel,
  LayoutDashboard,
  LogOut,
  CircleUserRound,
  ReceiptText,
  Users,
  Wheat,
  type LucideIcon,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import type { RoleName } from "../../types";

interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  roles: RoleName[];
}

const items: NavItem[] = [
  { label: "Resumen", to: "/app", icon: LayoutDashboard, roles: ["ADMINISTRADOR", "GANADERO", "COMPRADOR"] },
  { label: "Usuarios", to: "/app/users", icon: Users, roles: ["ADMINISTRADOR"] },
  { label: "Razas", to: "/app/breeds", icon: Beef, roles: ["ADMINISTRADOR", "GANADERO", "COMPRADOR"] },
  { label: "Lotes de ganado", to: "/app/lots", icon: Wheat, roles: ["ADMINISTRADOR", "GANADERO"] },
  { label: "Subastas", to: "/app/auctions", icon: Gavel, roles: ["ADMINISTRADOR", "GANADERO", "COMPRADOR"] },
  { label: "Mis pujas", to: "/app/bids", icon: Activity, roles: ["ADMINISTRADOR", "COMPRADOR"] },
  { label: "Adjudicaciones", to: "/app/adjudications", icon: ReceiptText, roles: ["ADMINISTRADOR", "COMPRADOR"] },
];

export function Sidebar({ onSignOut }: { onSignOut: () => void }) {
  const { user, roles } = useAuth();
  return (
    <aside className="sidebar">
      <NavLink to="/app" className="brand">
        <span className="brand-mark">S</span>
        <span>SUBAST<span className="brand-gold">AGRO</span><small>GANADO · CONFIANZA · VALOR</small></span>
      </NavLink>
      <div className="side-label">ESPACIO DE TRABAJO</div>
      <nav className="side-nav">
        {items.filter((item) => item.roles.some((role) => roles.includes(role))).map(({ label, to, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/app"} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            <Icon size={18} /><span>{label}</span>
          </NavLink>
        ))}
        <NavLink to="/app/profile" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          <CircleUserRound size={18} /><span>Mi perfil</span>
        </NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="user-mini">
          <span className="avatar">{user?.nombre_completo.slice(0, 1).toUpperCase()}</span>
          <span className="user-mini-name">{user?.nombre_completo}<small>{roles[0]?.replaceAll("_", " ")}</small></span>
        </div>
        <button className="nav-link signout" onClick={onSignOut}><LogOut size={18} /><span>Cerrar sesión</span></button>
      </div>
    </aside>
  );
}

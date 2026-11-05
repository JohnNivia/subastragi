import { Bell, Menu } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { useApiHealth } from "../../context/ApiHealthContext";

export function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { user } = useAuth();
  const apiStatus = useApiHealth();
  const initials = user?.nombre_completo.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  return (
    <header className="topbar">
      <button className="icon-button mobile-menu" aria-label="Abrir navegación" onClick={onMenuClick}><Menu size={21} /></button>
      <div className="topbar-context"><span>PLATAFORMA GANADERA</span><strong>Mercado transparente, oportunidades reales</strong></div>
      <div className="topbar-user">
        <span className={`api-status api-${apiStatus}`} title={`Backend: ${apiStatus}`}><i />API {apiStatus === "checking" ? "..." : apiStatus === "online" ? "en línea" : "sin conexión"}</span>
        <button className="icon-button notification-button" aria-label="Notificaciones informativas"><Bell size={18} /></button>
        <div><strong>{user?.nombre_completo}</strong><span>Cuenta verificada</span></div>
        <span className="avatar avatar-small">{initials}</span>
      </div>
    </header>
  );
}

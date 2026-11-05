import { Link, Outlet } from "react-router-dom";
import { Beef, ShieldCheck, TrendingUp } from "lucide-react";

export function AuthLayout() {
  return (
    <main className="auth-page">
      <section className="auth-story">
        <Link to="/login" className="brand auth-brand"><span className="brand-mark">S</span><span>SUBAST<span className="brand-gold">AGRO</span><small>GANADO · CONFIANZA · VALOR</small></span></Link>
        <div className="story-copy">
          <p className="eyebrow">EL CAMPO SE ENCUENTRA CON EL MERCADO</p>
          <h1>Una mejor forma de hacer negocio ganadero.</h1>
          <p>Conecta lotes de calidad con compradores en un espacio seguro, transparente y creado para el sector.</p>
          <div className="story-points">
            <span><Beef size={19} /> Oferta ganadera verificada</span>
            <span><TrendingUp size={19} /> Pujas claras y competitivas</span>
            <span><ShieldCheck size={19} /> Operaciones con trazabilidad</span>
          </div>
        </div>
        <div className="story-foot">SUBASTAGRO <span>·</span> COLOMBIA</div>
      </section>
      <section className="auth-panel"><Outlet /></section>
    </main>
  );
}

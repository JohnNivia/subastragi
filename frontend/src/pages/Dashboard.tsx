import { useEffect, useState } from "react";
import { Activity, Beef, Gavel, ReceiptText, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ErrorMessage, LoadingState } from "../components/common/Feedback";
import { PageHeader } from "../components/common/PageHeader";
import { StatCard } from "../components/common/StatCard";
import { StatusBadge } from "../components/common/StatusBadge";
import {
  adjudicationService,
  auctionService,
  bidService,
  lotService,
  userService,
} from "../services/api";
import type { Adjudication, Auction, Bid, CattleLot, User } from "../types";

export default function Dashboard() {
  const { user, roles } = useAuth();
  const isAdmin = roles.includes("ADMINISTRADOR");
  const isRancher = roles.includes("GANADERO");
  const isBuyer = roles.includes("COMPRADOR");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState({
    auctions: [] as Auction[],
    lots: [] as CattleLot[],
    bids: [] as Bid[],
    adjudications: [] as Adjudication[],
    users: [] as User[],
  });

  useEffect(() => {
    let active = true;
    const jobs: Promise<unknown>[] = [auctionService.list()];
    if (isAdmin || isRancher) jobs.push(lotService.list());
    if (isAdmin || isBuyer) jobs.push(bidService.list(), adjudicationService.list());
    if (isAdmin) jobs.push(userService.list());
    Promise.allSettled(jobs).then((results) => {
      if (!active) return;
      const failures = results.filter((result) => result.status === "rejected");
      if (failures.length) setError("Algunos indicadores no se pudieron cargar; revisa tu conexión o permisos.");
      const values = results.map((result) => result.status === "fulfilled" ? result.value : []);
      let index = 0;
      const auctions = values[index++] as Auction[];
      const lots = (isAdmin || isRancher ? values[index++] : []) as CattleLot[];
      const bids = (isAdmin || isBuyer ? values[index++] : []) as Bid[];
      const adjudications = (isAdmin || isBuyer ? values[index++] : []) as Adjudication[];
      const users = (isAdmin ? values[index++] : []) as User[];
      setData({ auctions, lots, bids, adjudications, users });
      setLoading(false);
    });
    return () => { active = false; };
  }, [isAdmin, isRancher, isBuyer]);

  if (loading) return <LoadingState />;

  return (
    <>
      <PageHeader eyebrow="RESUMEN DE OPERACIONES" title={`Bienvenido, ${user?.nombre_completo.split(" ")[0] ?? "a SubastAgro"}.`} description="Aquí tienes un panorama actualizado de tu actividad en la plataforma." />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <section className="stats-grid">
        {isAdmin && <StatCard icon={Users} label="Usuarios registrados" value={data.users.length} note="Cuentas en el sistema" />}
        {(isAdmin || isRancher) && <StatCard icon={Beef} label="Lotes visibles" value={data.lots.length} note="Según permisos de tu cuenta" />}
        <StatCard icon={Gavel} label="Subastas disponibles" value={data.auctions.length} note={isBuyer ? "Eventos activos para compradores" : "Eventos de tu operación"} />
        {(isAdmin || isBuyer) && <StatCard icon={Activity} label="Pujas registradas" value={data.bids.length} note={isAdmin ? "Actividad global reciente" : "Tu historial de ofertas"} />}
        {(isAdmin || isBuyer) && <StatCard icon={ReceiptText} label="Adjudicaciones" value={data.adjudications.length} note="Actas accesibles para tu perfil" />}
      </section>
      <div className="dashboard-grid">
        <section className="surface-card">
          <div className="section-heading"><div><p className="eyebrow">MERCADO</p><h2>Subastas recientes</h2></div><Link className="text-link" to="/app/auctions">Ver subastas →</Link></div>
          {data.auctions.length ? <div className="compact-list">{data.auctions.slice(0, 5).map((auction) => <div className="compact-row" key={auction.id}><span className="compact-mark"><Gavel size={17} /></span><div className="compact-main"><strong>{auction.estado_subasta.replaceAll("_", " ")}</strong><small>Lote {auction.lote_id}</small></div><StatusBadge value={auction.estado_subasta} /></div>)}</div> : <p className="muted">No hay subastas visibles para tu perfil.</p>}
        </section>
        <section className="surface-card highlight-card">
          <p className="eyebrow">TU SIGUIENTE PASO</p>
          <h2>{isAdmin ? "Mantén el mercado en movimiento." : isRancher ? "Presenta tu próximo lote." : "Encuentra tu próxima oportunidad."}</h2>
          <p>{isAdmin ? "Supervisa cuentas, oferta ganadera y el cierre responsable de cada evento." : isRancher ? "Registra un lote disponible y programa una subasta con fechas claras." : "Explora los eventos activos y realiza ofertas competitivas por kilo."}</p>
          <Link className="button button-primary" to={isAdmin ? "/app/users" : isRancher ? "/app/lots" : "/app/auctions"}>{isAdmin ? "Gestionar usuarios" : isRancher ? "Gestionar lotes" : "Explorar subastas"}</Link>
        </section>
      </div>
    </>
  );
}

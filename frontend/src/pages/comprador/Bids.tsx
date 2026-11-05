import { useCallback, useEffect, useState } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { getApiError } from "../../api/axios";
import { EmptyState, ErrorMessage, LoadingState } from "../../components/common/Feedback";
import { PageHeader } from "../../components/common/PageHeader";
import { bidService } from "../../services/api";
import type { Bid } from "../../types";

export default function Bids() {
  const [bids, setBids] = useState<Bid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      setBids(await bidService.list());
      setError(null);
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  return (
    <>
      <PageHeader eyebrow="ACTIVIDAD DEL COMPRADOR" title="Mis pujas" description="Consulta las ofertas realizadas con tu sesión. El backend limita esta lista a tus propias pujas." action={<button className="button button-outline" onClick={() => void load()}><RefreshCw size={16} /> Actualizar</button>} />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <section className="surface-card table-card"><div className="section-heading"><div><p className="eyebrow">HISTORIAL</p><h2>{bids.length} ofertas</h2></div><span className="stat-icon"><Activity size={19} /></span></div>
        {loading ? <LoadingState /> : bids.length === 0 ? <EmptyState>Todavía no has realizado ofertas. Explora las subastas activas para participar.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Evento</th><th>Precio ofertado por kg</th><th>Fecha y hora</th><th>Referencia</th></tr></thead><tbody>{bids.map((bid) => <tr key={bid.id}><td><strong>{bid.subasta_id.slice(0, 12).toUpperCase()}</strong></td><td>{Number(bid.monto_ofertado_kilo).toLocaleString("es-CO", { style: "currency", currency: "COP" })}</td><td>{new Date(bid.fecha_hora_puja).toLocaleString("es-CO")}</td><td><small>{bid.id}</small></td></tr>)}</tbody></table></div>}
      </section>
    </>
  );
}

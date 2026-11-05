import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Check, RefreshCw } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { getApiError } from "../../api/axios";
import { EmptyState, ErrorMessage, LoadingState, SuccessMessage } from "../../components/common/Feedback";
import { Field } from "../../components/common/Field";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { adjudicationService } from "../../services/api";
import type { Adjudication } from "../../types";

export default function Adjudications() {
  const { roles } = useAuth();
  const isAdmin = roles.includes("ADMINISTRADOR");
  const [items, setItems] = useState<Adjudication[]>([]);
  const [auctionId, setAuctionId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [busyClose, setBusyClose] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await adjudicationService.list());
      setError(null);
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const closeAuction = async (event: FormEvent) => {
    event.preventDefault();
    setBusyClose(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await adjudicationService.closeAuction(auctionId);
      setSuccess(result ? `Acta generada: ${result.guia_movilizacion_codigo}` : "La subasta se cerró sin pujas; quedó desierta y no se generó acta.");
      setAuctionId("");
      await load();
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setBusyClose(false);
    }
  };

  const updatePayment = async (item: Adjudication, status: string) => {
    setBusyId(item.id);
    setError(null);
    setSuccess(null);
    try {
      await adjudicationService.updatePayment(item.id, status);
      setSuccess("Se actualizó el estado de pago.");
      await load();
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <>
      <PageHeader eyebrow="CIERRE Y TRAZABILIDAD" title="Actas de adjudicación" description={isAdmin ? "Cierra subastas vencidas, consulta actas y actualiza el estado de pago." : "Consulta las actas de las subastas que has ganado."} action={<button className="button button-outline" onClick={() => void load()}><RefreshCw size={16} /> Actualizar</button>} />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      {isAdmin && <section className="surface-card form-card"><div className="section-heading"><div><p className="eyebrow">ACCIÓN ADMINISTRATIVA</p><h2>Cerrar subasta vencida</h2></div></div>
        <form className="inline-form" onSubmit={closeAuction}><Field label="ID de subasta (UUID)" name="auction_id" value={auctionId} onChange={(event) => setAuctionId(event.target.value)} required /><button className="button button-primary" disabled={busyClose}>{busyClose ? "Procesando..." : "Cerrar y generar acta"}</button></form>
        <p className="muted small">El backend rechaza el cierre antes de la fecha fin. Si no existen pujas, el evento queda DESIERTA y responde sin acta.</p>
      </section>}
      <section className="surface-card table-card"><div className="section-heading"><div><p className="eyebrow">REGISTRO FINANCIERO</p><h2>{items.length} actas</h2></div></div>
        {loading ? <LoadingState /> : items.length === 0 ? <EmptyState>No hay actas asociadas a esta cuenta.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Evento</th><th>Monto total</th><th>Guía de movilización</th><th>Estado de pago</th><th>Fecha de cierre</th>{isAdmin && <th>Actualizar pago</th>}</tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><strong>{item.subasta_id.slice(0, 12).toUpperCase()}</strong></td><td>{Number(item.monto_total_final).toLocaleString("es-CO", { style: "currency", currency: "COP" })}</td><td><code>{item.guia_movilizacion_codigo}</code></td><td><StatusBadge value={item.estado_pago} /></td><td>{new Date(item.fecha_cierre).toLocaleString("es-CO")}</td>{isAdmin && <td><div className="payment-actions">{(["PENDIENTE", "PAGADO", "RECHAZADO"] as const).map((status) => <button key={status} className={`button button-tiny ${item.estado_pago === status ? "button-selected" : "button-outline"}`} disabled={busyId === item.id || item.estado_pago === status} onClick={() => void updatePayment(item, status)}>{item.estado_pago === status && <Check size={12} />}{status}</button>)}</div></td>}</tr>)}</tbody></table></div>}
      </section>
    </>
  );
}

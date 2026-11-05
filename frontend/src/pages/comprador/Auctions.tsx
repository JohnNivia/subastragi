import { useCallback, useEffect, useState, type FormEvent } from "react";
import { CalendarClock, Gavel, Pencil, Plus, RefreshCw, X } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { getApiError } from "../../api/axios";
import { EmptyState, ErrorMessage, LoadingState, SuccessMessage } from "../../components/common/Feedback";
import { Field } from "../../components/common/Field";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { auctionService, bidService } from "../../services/api";
import type { Auction } from "../../types";

type AuctionForm = {
  lote_id: string;
  precio_base_kilo: string;
  incremento_minimo_puja: string;
  fecha_inicio: string;
  fecha_cierre: string;
};

const emptyForm: AuctionForm = {
  lote_id: "",
  precio_base_kilo: "",
  incremento_minimo_puja: "",
  fecha_inicio: "",
  fecha_cierre: "",
};

function localDateTime(value: string): string {
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

export default function Auctions() {
  const { roles } = useAuth();
  const canSchedule = roles.includes("ADMINISTRADOR") || roles.includes("GANADERO");
  const isBuyer = roles.includes("COMPRADOR");
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [form, setForm] = useState<AuctionForm>(emptyForm);
  const [editing, setEditing] = useState<Auction | null>(null);
  const [selectedAuction, setSelectedAuction] = useState<Auction | null>(null);
  const [bidValue, setBidValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAuctions(await auctionService.list());
      setError(null);
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const submitAuction = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    const payload = {
      lote_id: form.lote_id,
      precio_base_kilo: Number(form.precio_base_kilo),
      incremento_minimo_puja: Number(form.incremento_minimo_puja),
      fecha_inicio: new Date(form.fecha_inicio).toISOString(),
      fecha_cierre: new Date(form.fecha_cierre).toISOString(),
    };
    try {
      if (editing) {
        const { lote_id: _loteId, ...updates } = payload;
        await auctionService.update(editing.id, updates);
        setSuccess("Se actualizaron los datos de la subasta.");
      } else {
        await auctionService.create(payload);
        setSuccess("La subasta quedó programada.");
      }
      setEditing(null);
      setForm(emptyForm);
      await load();
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setBusy(false);
    }
  };

  const startEdit = (auction: Auction) => {
    setEditing(auction);
    setForm({
      lote_id: auction.lote_id,
      precio_base_kilo: String(auction.precio_base_kilo),
      incremento_minimo_puja: String(auction.incremento_minimo_puja),
      fecha_inicio: localDateTime(auction.fecha_inicio),
      fecha_cierre: localDateTime(auction.fecha_cierre),
    });
    setSuccess(null);
  };

  const submitBid = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedAuction) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      await bidService.create({
        subasta_id: selectedAuction.id,
        monto_ofertado_kilo: Number(bidValue),
      });
      setSuccess(`Oferta registrada para el evento ${selectedAuction.id}.`);
      setBidValue("");
      setSelectedAuction(null);
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setBusy(false);
    }
  };

  const set = (key: keyof AuctionForm, value: string) => setForm((current) => ({ ...current, [key]: value }));

  return (
    <>
      <PageHeader eyebrow="MERCADO GANADERO" title={isBuyer ? "Subastas activas" : "Eventos de subasta"} description={isBuyer ? "Explora los eventos abiertos y presenta una oferta por kilo." : "Programa y consulta los eventos vinculados a lotes de ganado."} action={<button className="button button-outline" onClick={() => void load()}><RefreshCw size={16} /> Actualizar</button>} />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      {canSchedule && <section className="surface-card form-card">
        <div className="section-heading"><div><p className="eyebrow">{editing ? "CAMBIOS DEL EVENTO" : "NUEVO EVENTO"}</p><h2>{editing ? "Editar subasta programada" : "Programar subasta"}</h2></div>{editing && <button className="icon-button" aria-label="Cancelar edición" onClick={() => { setEditing(null); setForm(emptyForm); }}><X size={18} /></button>}</div>
        <form className="form-grid" onSubmit={submitAuction}>
          <Field label="ID del lote (UUID)" name="lote_id" value={form.lote_id} onChange={(event) => set("lote_id", event.target.value)} disabled={Boolean(editing)} required />
          <Field label="Precio base por kilo" name="precio_base_kilo" type="number" min="0.01" step="0.01" value={form.precio_base_kilo} onChange={(event) => set("precio_base_kilo", event.target.value)} required />
          <Field label="Incremento mínimo por kilo" name="incremento_minimo_puja" type="number" min="0.01" step="0.01" value={form.incremento_minimo_puja} onChange={(event) => set("incremento_minimo_puja", event.target.value)} required />
          <Field label="Inicio (hora local)" name="fecha_inicio" type="datetime-local" value={form.fecha_inicio} onChange={(event) => set("fecha_inicio", event.target.value)} required />
          <Field label="Cierre (hora local)" name="fecha_cierre" type="datetime-local" value={form.fecha_cierre} onChange={(event) => set("fecha_cierre", event.target.value)} required />
          <div className="form-actions"><button className="button button-primary" disabled={busy}>{busy ? "Guardando..." : editing ? "Guardar cambios" : <><Plus size={17} /> Programar evento</>}</button></div>
        </form>
      </section>}
      <section className="auction-grid">
        {loading ? <LoadingState /> : auctions.length === 0 ? <EmptyState>No hay subastas visibles para tu perfil en este momento.</EmptyState> : auctions.map((auction) => (
          <article className="auction-card" key={auction.id}>
            <div className="auction-card-top"><span className="auction-icon"><Gavel size={19} /></span><StatusBadge value={auction.estado_subasta} /></div>
            <p className="eyebrow">EVENTO {auction.id.slice(0, 8).toUpperCase()}</p>
            <h2>Lote {auction.lote_id.slice(0, 8).toUpperCase()}</h2>
            <div className="auction-price"><span>Precio base</span><strong>{Number(auction.precio_base_kilo).toLocaleString("es-CO", { style: "currency", currency: "COP" })}<small> / kg</small></strong></div>
            <div className="auction-meta"><span><CalendarClock size={15} /> Inicia {new Date(auction.fecha_inicio).toLocaleString("es-CO")}</span><span><CalendarClock size={15} /> Cierra {new Date(auction.fecha_cierre).toLocaleString("es-CO")}</span></div>
            <div className="auction-actions">
              {isBuyer && auction.estado_subasta === "ACTIVA" && <button className="button button-primary button-small" onClick={() => { setSelectedAuction(auction); setBidValue(String(Number(auction.precio_base_kilo) + Number(auction.incremento_minimo_puja))); }}><Gavel size={15} /> Ofertar</button>}
              {canSchedule && auction.estado_subasta === "PROGRAMADA" && <button className="button button-outline button-small" onClick={() => startEdit(auction)}><Pencil size={15} /> Editar</button>}
            </div>
          </article>
        ))}
      </section>
      {selectedAuction && <section className="surface-card form-card bid-composer">
        <div className="section-heading"><div><p className="eyebrow">OFERTA POR KILO</p><h2>Nueva puja</h2><p className="muted">El servidor valida la oferta mínima vigente, incluida la puja máxima de otros compradores.</p></div><button className="icon-button" aria-label="Cancelar puja" onClick={() => setSelectedAuction(null)}><X size={18} /></button></div>
        <form className="inline-form" onSubmit={submitBid}><Field label="Precio ofertado por kilo (COP)" name="monto_ofertado_kilo" type="number" min={Number(selectedAuction.precio_base_kilo)} step="0.01" value={bidValue} onChange={(event) => setBidValue(event.target.value)} required /><button className="button button-primary" disabled={busy}>{busy ? "Enviando..." : "Confirmar puja"}</button></form>
      </section>}
      <p className="backend-note">Por control de acceso, el backend actual no permite a compradores consultar el detalle del lote ni las ofertas de terceros. La tarjeta muestra los datos expuestos por el endpoint de subastas.</p>
    </>
  );
}

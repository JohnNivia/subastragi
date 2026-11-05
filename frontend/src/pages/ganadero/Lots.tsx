import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Check, Pencil, Plus, RefreshCw, X } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { ErrorMessage, LoadingState, SuccessMessage, EmptyState } from "../../components/common/Feedback";
import { Field, SelectField } from "../../components/common/Field";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { lotService, breedService } from "../../services/api";
import type { Breed, CattleLot } from "../../types";

const initialForm = {
  raza_id: "",
  codigo_lote: "",
  cantidad_cabezas: "1",
  peso_promedio_kg: "400",
  vacunacion_al_dia: "true",
  ubicacion_hacienda: "",
};

export default function Lots() {
  const { roles } = useAuth();
  const isAdmin = roles.includes("ADMINISTRADOR");
  const isRancher = roles.includes("GANADERO");
  const [lots, setLots] = useState<CattleLot[]>([]);
  const [breeds, setBreeds] = useState<Breed[]>([]);
  const [form, setForm] = useState(initialForm);
  const [editing, setEditing] = useState<CattleLot | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [lotData, breedData] = await Promise.all([lotService.list(), breedService.list()]);
      setLots(lotData);
      setBreeds(breedData);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudieron cargar los lotes.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      if (editing) {
        await lotService.update(editing.id, {
          raza_id: form.raza_id,
          cantidad_cabezas: Number(form.cantidad_cabezas),
          peso_promedio_kg: Number(form.peso_promedio_kg),
          vacunacion_al_dia: form.vacunacion_al_dia === "true",
          ubicacion_hacienda: form.ubicacion_hacienda,
        });
        setSuccess("El lote se actualizó correctamente.");
      } else {
        await lotService.create({
          raza_id: form.raza_id,
          codigo_lote: form.codigo_lote,
          cantidad_cabezas: Number(form.cantidad_cabezas),
          peso_promedio_kg: Number(form.peso_promedio_kg),
          vacunacion_al_dia: form.vacunacion_al_dia === "true",
          ubicacion_hacienda: form.ubicacion_hacienda,
        });
        setSuccess("El lote quedó registrado.");
      }
      setEditing(null);
      setForm(initialForm);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo guardar el lote.");
    } finally {
      setBusy(false);
    }
  };

  const beginEdit = (lot: CattleLot) => {
    setEditing(lot);
    setForm({
      ...initialForm,
      raza_id: lot.raza_id,
      codigo_lote: lot.codigo_lote,
      cantidad_cabezas: String(lot.cantidad_cabezas),
      peso_promedio_kg: String(lot.peso_promedio_kg),
      vacunacion_al_dia: String(lot.vacunacion_al_dia),
      ubicacion_hacienda: lot.ubicacion_hacienda,
    });
    setSuccess(null);
  };

  const changeStatus = async (lot: CattleLot) => {
    const next = lot.estado_lote === "SUSPENDIDO" ? "DISPONIBLE" : "SUSPENDIDO";
    setError(null);
    try {
      await lotService.updateStatus(lot.id, next);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo cambiar el estado.");
    }
  };

  const set = (key: keyof typeof initialForm, value: string) => setForm((current) => ({ ...current, [key]: value }));

  return (
    <>
      <PageHeader eyebrow="INVENTARIO GANADERO" title="Lotes de ganado" description={isAdmin ? "Consulta la oferta registrada por los ganaderos y modera su disponibilidad." : "Administra tus lotes, datos sanitarios y disponibilidad para subastas."} action={<button className="button button-outline" onClick={() => void load()}><RefreshCw size={16} /> Actualizar</button>} />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      {isRancher && <section className="surface-card form-card">
        <div className="section-heading"><div><p className="eyebrow">{editing ? "ACTUALIZACIÓN" : "NUEVA OFERTA"}</p><h2>{editing ? `Editar ${editing.codigo_lote}` : "Registrar lote"}</h2></div>{editing && <button className="icon-button" aria-label="Cancelar edición" onClick={() => { setEditing(null); setForm(initialForm); }}><X size={18} /></button>}</div>
        <form className="form-grid" onSubmit={submit}>
          {!editing && <Field label="Código del lote" name="codigo_lote" pattern="[A-Za-z0-9_-]+" minLength={3} maxLength={40} value={form.codigo_lote} onChange={(event) => set("codigo_lote", event.target.value)} required />}
          <SelectField label="Raza" name="raza_id" value={form.raza_id} onChange={(event) => set("raza_id", event.target.value)} required>
            <option value="">Selecciona una raza</option>{breeds.filter((breed) => breed.estado).map((breed) => <option key={breed.id} value={breed.id}>{breed.nombre_raza} · {breed.proposito}</option>)}
          </SelectField>
          <Field label="Cantidad de cabezas" name="cantidad_cabezas" type="number" min="1" max="100000" value={form.cantidad_cabezas} onChange={(event) => set("cantidad_cabezas", event.target.value)} required />
          <Field label="Peso promedio (kg)" name="peso_promedio_kg" type="number" min="0.1" max="2000" step="0.1" value={form.peso_promedio_kg} onChange={(event) => set("peso_promedio_kg", event.target.value)} required />
          <Field label="Ubicación de la hacienda" name="ubicacion_hacienda" minLength={2} maxLength={180} value={form.ubicacion_hacienda} onChange={(event) => set("ubicacion_hacienda", event.target.value)} required />
          <SelectField label="Vacunación al día" name="vacunacion_al_dia" value={form.vacunacion_al_dia} onChange={(event) => set("vacunacion_al_dia", event.target.value)}><option value="true">Sí, al día</option><option value="false">No</option></SelectField>
          <div className="form-actions"><button className="button button-primary" disabled={busy || breeds.length === 0}>{busy ? "Guardando..." : editing ? "Guardar cambios" : <><Plus size={17} /> Registrar lote</>}</button>{breeds.length === 0 && <span className="muted small">El catálogo no tiene razas habilitadas.</span>}</div>
        </form>
      </section>}
      <section className="surface-card table-card">
        <div className="section-heading"><div><p className="eyebrow">GANADO REGISTRADO</p><h2>{lots.length} lotes</h2></div></div>
        {loading ? <LoadingState /> : lots.length === 0 ? <EmptyState>Aún no hay lotes disponibles para esta cuenta.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Lote</th><th>Volumen</th><th>Peso promedio</th><th>Ubicación</th><th>Sanidad</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>
          {lots.map((lot) => <tr key={lot.id}><td><strong>{lot.codigo_lote}</strong><small className="cell-sub">{lot.id}</small></td><td>{lot.cantidad_cabezas} cabezas</td><td>{lot.peso_promedio_kg.toLocaleString("es-CO")} kg</td><td>{lot.ubicacion_hacienda}</td><td><StatusBadge value={lot.vacunacion_al_dia ? "VACUNADO" : "PENDIENTE"} /></td><td><StatusBadge value={lot.estado_lote} /></td><td><div className="row-actions">{isRancher && <button className="icon-button" title="Editar lote" onClick={() => beginEdit(lot)}><Pencil size={16} /></button>}{isAdmin && lot.estado_lote !== "EN_SUBASTA" && lot.estado_lote !== "ADJUDICADO" && <button className="icon-button" title={lot.estado_lote === "SUSPENDIDO" ? "Habilitar lote" : "Suspender lote"} onClick={() => void changeStatus(lot)}>{lot.estado_lote === "SUSPENDIDO" ? <Check size={16} /> : <X size={16} />}</button>}</div></td></tr>)}
        </tbody></table></div>}
      </section>
    </>
  );
}

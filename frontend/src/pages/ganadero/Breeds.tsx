import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Check, Plus, RefreshCw, X } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { EmptyState, ErrorMessage, LoadingState, SuccessMessage } from "../../components/common/Feedback";
import { Field } from "../../components/common/Field";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { breedService } from "../../services/api";
import type { Breed } from "../../types";

export default function Breeds() {
  const { roles } = useAuth();
  const isAdmin = roles.includes("ADMINISTRADOR");
  const [breeds, setBreeds] = useState<Breed[]>([]);
  const [name, setName] = useState("");
  const [purpose, setPurpose] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setBreeds(await breedService.list());
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo consultar el catálogo.");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      await breedService.create({ nombre_raza: name, proposito: purpose });
      setName("");
      setPurpose("");
      setSuccess("La raza se agregó al catálogo.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo guardar la raza.");
    } finally {
      setBusy(false);
    }
  };

  const toggleBreed = async (breed: Breed) => {
    try {
      await breedService.update(breed.id, { estado: !breed.estado });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo actualizar la raza.");
    }
  };

  return (
    <>
      <PageHeader eyebrow="CATÁLOGO DE GANADO" title="Razas" description="Consulta las razas habilitadas para registrar lotes de ganado." action={<button className="button button-outline" onClick={() => void load()}><RefreshCw size={16} /> Actualizar</button>} />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      {isAdmin && <section className="surface-card form-card"><div className="section-heading"><div><p className="eyebrow">ADMINISTRACIÓN</p><h2>Agregar raza</h2></div></div>
        <form className="form-grid compact-form" onSubmit={create}><Field label="Nombre de raza" name="nombre_raza" minLength={2} maxLength={80} value={name} onChange={(event) => setName(event.target.value)} required /><Field label="Propósito" name="proposito" minLength={2} maxLength={40} value={purpose} onChange={(event) => setPurpose(event.target.value)} placeholder="Carne, leche, doble propósito" required /><div className="form-actions"><button className="button button-primary" disabled={busy}>{busy ? "Guardando..." : <><Plus size={17} /> Crear raza</>}</button></div></form>
      </section>}
      <section className="surface-card table-card"><div className="section-heading"><div><p className="eyebrow">CATÁLOGO VIGENTE</p><h2>{breeds.length} razas</h2></div></div>
        {loading ? <LoadingState /> : breeds.length === 0 ? <EmptyState>No se encontraron razas en el catálogo.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Raza</th><th>Propósito</th><th>Disponibilidad</th>{isAdmin && <th>Acción</th>}</tr></thead><tbody>{breeds.map((breed) => <tr key={breed.id}><td><strong>{breed.nombre_raza}</strong></td><td>{breed.proposito}</td><td><StatusBadge value={breed.estado ? "ACTIVA" : "SUSPENDIDA"} /></td>{isAdmin && <td><button className="icon-button" title={breed.estado ? "Deshabilitar" : "Habilitar"} onClick={() => void toggleBreed(breed)}>{breed.estado ? <X size={16} /> : <Check size={16} />}</button></td>}</tr>)}</tbody></table></div>}
      </section>
    </>
  );
}

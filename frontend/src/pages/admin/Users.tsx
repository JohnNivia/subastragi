import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Check, Plus, RefreshCw, ShieldCheck, UserRound } from "lucide-react";
import { getApiError } from "../../api/axios";
import { ErrorMessage, EmptyState, LoadingState, SuccessMessage } from "../../components/common/Feedback";
import { Field, SelectField } from "../../components/common/Field";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { authService, userService } from "../../services/api";
import type { RegisterPayload, RoleName, User } from "../../types";

const blankUser: RegisterPayload = {
  email: "",
  password: "",
  nombre_completo: "",
  documento_identidad: "",
  telefono: "",
  rol: "COMPRADOR",
};

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(blankUser);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setUsers(await userService.list());
      setError(null);
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const createUser = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      await authService.register({ ...form, telefono: form.telefono || null });
      setForm(blankUser);
      setShowCreate(false);
      setSuccess("La cuenta se creó correctamente. El registro no permite asignar el rol de administrador.");
      await load();
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setBusy(false);
    }
  };

  const updateUser = async (user: User, changes: Record<string, unknown>, message: string) => {
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      await userService.update(user.id, changes);
      setSuccess(message);
      await load();
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setBusy(false);
    }
  };

  const changeRole = (user: User, role: RoleName) => {
    void updateUser(user, { roles: [role] }, `Se actualizó el rol de ${user.nombre_completo}.`);
  };

  const set = (key: keyof RegisterPayload, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  return (
    <>
      <PageHeader eyebrow="CONTROL DE ACCESO" title="Usuarios y roles" description="Administra las cuentas, su estado y los permisos asignados." action={<><button className="button button-outline" onClick={() => void load()}><RefreshCw size={16} /> Actualizar</button><button className="button button-primary" onClick={() => setShowCreate((current) => !current)}><Plus size={17} /> Crear cuenta</button></>} />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      {showCreate && <section className="surface-card form-card"><div className="section-heading"><div><p className="eyebrow">ALTA DE CUENTA</p><h2>Registrar ganadero o comprador</h2></div></div>
        <form className="form-grid" onSubmit={createUser}>
          <Field label="Nombre completo" name="nombre_completo" minLength={2} maxLength={160} value={form.nombre_completo} onChange={(event) => set("nombre_completo", event.target.value)} required />
          <Field label="Correo electrónico" name="email" type="email" value={form.email} onChange={(event) => set("email", event.target.value)} required />
          <Field label="Documento de identidad" name="documento_identidad" minLength={5} maxLength={40} value={form.documento_identidad} onChange={(event) => set("documento_identidad", event.target.value)} required />
          <Field label="Teléfono" name="telefono" type="tel" maxLength={30} value={form.telefono ?? ""} onChange={(event) => set("telefono", event.target.value)} />
          <SelectField label="Rol inicial" name="rol" value={form.rol} onChange={(event) => set("rol", event.target.value as RegisterPayload["rol"])}><option value="COMPRADOR">COMPRADOR</option><option value="GANADERO">GANADERO</option></SelectField>
          <Field label="Contraseña temporal (mínimo 12 caracteres)" name="password" type="password" minLength={12} maxLength={72} value={form.password} onChange={(event) => set("password", event.target.value)} required />
          <div className="form-actions"><button className="button button-primary" disabled={busy}>{busy ? "Creando..." : "Crear cuenta"}</button></div>
        </form>
      </section>}
      <section className="stats-strip"><div><UserRound size={18} /><span>{users.length} cuentas</span></div><div><ShieldCheck size={18} /><span>Acceso con roles y estado de cuenta</span></div></section>
      <section className="surface-card table-card"><div className="section-heading"><div><p className="eyebrow">DIRECTORIO</p><h2>Usuarios registrados</h2></div></div>
        {loading ? <LoadingState /> : users.length === 0 ? <EmptyState>No hay usuarios registrados.</EmptyState> : <div className="table-scroll"><table><thead><tr><th>Usuario</th><th>Documento</th><th>Contacto</th><th>Rol(es)</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{users.map((user) => {
          const currentRole = user.roles[0]?.nombre_rol ?? "COMPRADOR";
          return <tr key={user.id}><td><strong>{user.nombre_completo}</strong><small className="cell-sub">{user.email}</small></td><td>{user.documento_identidad}</td><td>{user.telefono || "—"}</td><td><div className="role-cell"><StatusBadge value={currentRole} /><SelectField label="Cambiar rol" name={`role-${user.id}`} aria-label={`Cambiar rol de ${user.nombre_completo}`} value={currentRole} onChange={(event) => changeRole(user, event.target.value as RoleName)} disabled={busy}><option value="COMPRADOR">COMPRADOR</option><option value="GANADERO">GANADERO</option><option value="ADMINISTRADOR">ADMINISTRADOR</option></SelectField></div></td><td><StatusBadge value={user.estado ? "ACTIVA" : "INACTIVA"} /></td><td><button className={`button button-small ${user.estado ? "button-outline" : "button-primary"}`} disabled={busy} onClick={() => void updateUser(user, { estado: !user.estado }, `La cuenta quedó ${user.estado ? "desactivada" : "activada"}.`)}>{user.estado ? "Desactivar" : <><Check size={15} /> Activar</>}</button></td></tr>;
        })}</tbody></table></div>}
      </section>
    </>
  );
}

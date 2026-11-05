import { useState, type FormEvent } from "react";
import { Save, ShieldCheck, UserRound } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api, getApiError } from "../api/axios";
import { endpoints } from "../api/endpoints";
import { ErrorMessage, SuccessMessage } from "../components/common/Feedback";
import { Field } from "../components/common/Field";
import { PageHeader } from "../components/common/PageHeader";
import type { User } from "../types";

export default function Profile() {
  const { user, updateCurrentUser } = useAuth();
  const [name, setName] = useState(user?.nombre_completo ?? "");
  const [phone, setPhone] = useState(user?.telefono ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const { data } = await api.patch<User>(endpoints.users.me, {
        nombre_completo: name,
        telefono: phone || null,
      });
      setName(data.nombre_completo);
      setPhone(data.telefono ?? "");
      updateCurrentUser(data);
      setSuccess("Los datos del perfil se actualizaron.");
    } catch (reason) {
      setError(getApiError(reason));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader eyebrow="CUENTA PERSONAL" title="Mi perfil" description="Actualiza tus datos de contacto y consulta la información de tu cuenta." />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      <div className="profile-layout">
        <section className="surface-card profile-card"><span className="profile-avatar"><UserRound size={29} /></span><p className="eyebrow">PERFIL SUBASTAGRO</p><h2>{user?.nombre_completo}</h2><p>{user?.email}</p><div className="profile-roles">{user?.roles.map((role) => <span className="role-pill" key={role.id}><ShieldCheck size={14} />{role.nombre_rol.replaceAll("_", " ")}</span>)}</div><div className="profile-data"><span>Estado de cuenta</span><strong>{user?.estado ? "Activa" : "Inactiva"}</strong><span>Miembro desde</span><strong>{user?.fecha_creacion ? new Date(user.fecha_creacion).toLocaleDateString("es-CO") : "—"}</strong></div></section>
        <section className="surface-card form-card"><div className="section-heading"><div><p className="eyebrow">INFORMACIÓN PERSONAL</p><h2>Datos de contacto</h2></div></div><form className="form-stack" onSubmit={save}><Field label="Nombre completo" name="nombre_completo" minLength={2} maxLength={160} value={name} onChange={(event) => setName(event.target.value)} required /><Field label="Teléfono" name="telefono" type="tel" maxLength={30} value={phone} onChange={(event) => setPhone(event.target.value)} /><label className="field"><span>Correo electrónico</span><input value={user?.email ?? ""} disabled /></label><label className="field"><span>Documento de identidad</span><input value={user?.documento_identidad ?? ""} disabled /></label><button className="button button-primary align-start" disabled={busy}>{busy ? "Guardando..." : <><Save size={16} /> Guardar perfil</>}</button></form></section>
      </div>
    </>
  );
}

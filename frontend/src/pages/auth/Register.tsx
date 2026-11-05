import { useState, type FormEvent } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { ErrorMessage } from "../../components/common/Feedback";
import { Field, SelectField } from "../../components/common/Field";
import type { RegisterPayload } from "../../types";

export default function Register() {
  const { signUp, error, clearError } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<RegisterPayload>({
    email: "",
    password: "",
    nombre_completo: "",
    documento_identidad: "",
    telefono: "",
    rol: "COMPRADOR",
  });
  const set = (key: keyof RegisterPayload, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    clearError();
    setBusy(true);
    try {
      await signUp({ ...form, telefono: form.telefono || null });
      navigate("/login", { replace: true, state: { registered: true } });
    } catch {
      // The API error is shown by the authentication context.
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-card auth-card-register">
      <Link to="/login" className="back-link"><ArrowLeft size={16} /> Volver al acceso</Link>
      <div className="auth-card-heading"><p className="eyebrow">ÚNETE A SUBASTAGRO</p><h2>Tu siguiente gran negocio empieza aquí.</h2><p>Completa tus datos para crear una cuenta.</p></div>
      <form className="form-stack" onSubmit={submit}>
        {error && <ErrorMessage>{error}</ErrorMessage>}
        <Field label="Nombre completo" name="nombre_completo" autoComplete="name" minLength={2} maxLength={160} value={form.nombre_completo} onChange={(event) => set("nombre_completo", event.target.value)} required />
        <Field label="Correo electrónico" name="email" type="email" autoComplete="email" value={form.email} onChange={(event) => set("email", event.target.value)} required />
        <div className="form-row">
          <Field label="Documento de identidad" name="documento_identidad" minLength={5} maxLength={40} value={form.documento_identidad} onChange={(event) => set("documento_identidad", event.target.value)} required />
          <Field label="Teléfono (opcional)" name="telefono" type="tel" maxLength={30} value={form.telefono ?? ""} onChange={(event) => set("telefono", event.target.value)} />
        </div>
        <SelectField label="Perfil de cuenta" name="rol" value={form.rol} onChange={(event) => set("rol", event.target.value as RegisterPayload["rol"])}>
          <option value="COMPRADOR">Comprador de ganado</option>
          <option value="GANADERO">Ganadero / vendedor</option>
        </SelectField>
        <Field label="Contraseña (mínimo 12 caracteres)" name="password" type="password" autoComplete="new-password" minLength={12} maxLength={72} value={form.password} onChange={(event) => set("password", event.target.value)} required />
        <button className="button button-primary button-full" disabled={busy}>{busy ? "Creando cuenta..." : "Crear cuenta"} <ArrowRight size={17} /></button>
      </form>
      <p className="auth-footnote">El registro público no permite crear cuentas de administrador.</p>
    </div>
  );
}

import { useState, type FormEvent } from "react";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { ErrorMessage } from "../../components/common/Feedback";
import { Field } from "../../components/common/Field";

export default function Login() {
  const { signIn, error, clearError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    clearError();
    setBusy(true);
    try {
      await signIn(email, password);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from || "/app", { replace: true });
    } catch {
      // The authentication context retains the API error for display.
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-card">
      <div className="auth-card-heading"><span className="auth-icon"><LockKeyhole size={21} /></span><p className="eyebrow">ACCESO A TU CUENTA</p><h2>Qué bueno tenerte de vuelta.</h2><p>Ingresa tus credenciales para continuar.</p></div>
      <form className="form-stack" onSubmit={submit}>
        {error && <ErrorMessage>{error}</ErrorMessage>}
        <Field label="Correo electrónico" name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <Field label="Contraseña" name="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        <button className="button button-primary button-full" disabled={busy}>{busy ? "Validando..." : "Iniciar sesión"} <ArrowRight size={17} /></button>
      </form>
      <p className="auth-switch">¿Aún no tienes cuenta? <Link to="/register">Regístrate</Link></p>
      <p className="auth-footnote">La sesión se protege con token de acceso en memoria y cookie HttpOnly.</p>
    </div>
  );
}

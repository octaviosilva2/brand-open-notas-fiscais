/** Tela de login: autentica via AuthContext e redireciona ao destino original. */

import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { ApiError } from '../api/http';
import { Card, Field, TextInput } from '../components/primitives';

interface LocationState {
  from?: { pathname?: string };
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as LocationState | null)?.from?.pathname ?? '/clientes';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('E-mail ou senha inválidos.');
      } else {
        setError('Não foi possível entrar. Tente novamente.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <header className="app-bar">
        <span className="app-bar__emit">BRAND OPEN — Emissão de NFS-e</span>
      </header>
      <div className="login-wrap">
        <form className="login-card" onSubmit={onSubmit}>
          <Card title="Entrar">
            {error && <div className="banner banner--warn">{error}</div>}
            <Field label="E-mail" required>
              <TextInput type="email" value={email} onChange={setEmail} placeholder="voce@empresa.com" />
            </Field>
            <Field label="Senha" required>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Entrando...' : 'Entrar'}
            </button>
          </Card>
        </form>
      </div>
    </>
  );
}

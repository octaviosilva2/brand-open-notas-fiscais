/** Layout autenticado: app-bar com navegação e botão de sair + <Outlet/>. */

import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function AppLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  function onLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <>
      <header className="app-bar">
        <span className="app-bar__emit">BRAND OPEN — Emissão de NFS-e</span>
        <nav className="app-nav">
          <NavLink to="/clientes" className="app-nav__link">
            Clientes
          </NavLink>
          <NavLink to="/recorrencias" className="app-nav__link">
            Recorrências
          </NavLink>
          <NavLink to="/notas" className="app-nav__link">
            Notas
          </NavLink>
        </nav>
        <span className="app-bar__spacer" />
        <button type="button" className="btn btn-outline" onClick={onLogout}>
          Sair
        </button>
      </header>

      <main className="page">
        <Outlet />
      </main>
    </>
  );
}

/** Listagem de clientes: busca com debounce, paginação, estados, ações por linha. */

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useClients, useDeleteClient } from '../../features/clients/hooks';
import { backendMessage } from '../../features/clients/errors';
import type { Client } from '../../features/clients/types';

export function ClientsListPage() {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Debounce da busca; volta para a página 1 a cada nova busca.
  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  const { data, isLoading, isError, error } = useClients({ page, search });
  const del = useDeleteClient();

  async function onDelete(c: Client) {
    if (!window.confirm(`Excluir o cliente "${c.name}"?`)) return;
    setDeleteError(null);
    try {
      await del.mutateAsync(c.id);
    } catch (err) {
      setDeleteError(backendMessage(err, 'Não foi possível excluir o cliente.'));
    }
  }

  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;

  return (
    <>
      <div className="page-head">
        <div className="page-title">Clientes</div>
        <Link to="/clientes/novo" className="btn btn-primary">
          Novo cliente
        </Link>
      </div>

      {deleteError && <div className="banner banner--warn">{deleteError}</div>}

      <div className="toolbar">
        <input
          className="input toolbar__search"
          placeholder="Buscar por nome, documento ou e-mail..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
      </div>

      {isLoading && <div className="list-state">Carregando clientes...</div>}
      {isError && (
        <div className="banner banner--warn">{backendMessage(error, 'Falha ao carregar clientes.')}</div>
      )}

      {!isLoading && !isError && data && data.data.length === 0 && (
        <div className="list-state">Nenhum cliente encontrado.</div>
      )}

      {!isLoading && !isError && data && data.data.length > 0 && (
        <>
          <table className="table">
            <thead>
              <tr>
                <th>Documento</th>
                <th>Nome</th>
                <th>E-mail</th>
                <th>Telefone</th>
                <th>Ativo</th>
                <th aria-label="Ações" />
              </tr>
            </thead>
            <tbody>
              {data.data.map((c) => (
                <tr key={c.id}>
                  <td>
                    {c.document_type} {c.document}
                  </td>
                  <td>{c.name}</td>
                  <td>{c.email ?? '—'}</td>
                  <td>{c.phone ?? '—'}</td>
                  <td>{c.is_active ? 'Sim' : 'Não'}</td>
                  <td>
                    <div className="row-actions">
                      <button
                        type="button"
                        className="btn-link"
                        onClick={() => navigate(`/clientes/${c.id}`)}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="btn-danger-link"
                        onClick={() => onDelete(c)}
                        disabled={del.isPending}
                      >
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <span>
              {total} cliente(s) — página {page} de {totalPages}
            </span>
            <div className="row-actions">
              <button
                type="button"
                className="btn btn-outline"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </button>
              <button
                type="button"
                className="btn btn-outline"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Próxima
              </button>
            </div>
          </div>
        </>
      )}
    </>
  );
}

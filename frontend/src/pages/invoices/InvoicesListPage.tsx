/** Listagem de notas geradas (log): tabela com tomador/descrição/valor/status/
 *  agendamento/emissão, filtros (status, cliente, período) e paginação. */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useInvoices } from '../../features/invoices/hooks';
import { backendMessage } from '../../features/clients/errors';
import { STATUS_LABEL, formatAmount, formatDate, statusClass } from '../../features/invoices/format';
import type { InvoiceStatus } from '../../features/invoices/types';

type StatusFilter = 'todos' | InvoiceStatus;

export function InvoicesListPage() {
  const [status, setStatus] = useState<StatusFilter>('todos');
  const [clientId, setClientId] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error } = useInvoices({
    page,
    status: status === 'todos' ? undefined : status,
    client_id: clientId.trim() || undefined,
    from: from || undefined,
    to: to || undefined,
  });

  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;

  function resetPage<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v);
      setPage(1);
    };
  }

  return (
    <>
      <div className="page-head">
        <div className="page-title">Notas geradas</div>
      </div>

      <div className="toolbar">
        <select
          className="input"
          value={status}
          onChange={(e) => resetPage(setStatus)(e.target.value as StatusFilter)}
        >
          <option value="todos">Todos os status</option>
          <option value="pending">{STATUS_LABEL.pending}</option>
          <option value="processing">{STATUS_LABEL.processing}</option>
          <option value="success">{STATUS_LABEL.success}</option>
          <option value="error">{STATUS_LABEL.error}</option>
        </select>
        <input
          className="input toolbar__search"
          placeholder="Filtrar por ID do cliente..."
          value={clientId}
          onChange={(e) => resetPage(setClientId)(e.target.value)}
        />
        <input
          className="input"
          type="date"
          value={from}
          onChange={(e) => resetPage(setFrom)(e.target.value)}
          title="De"
        />
        <input
          className="input"
          type="date"
          value={to}
          onChange={(e) => resetPage(setTo)(e.target.value)}
          title="Até"
        />
      </div>

      {isLoading && <div className="list-state">Carregando notas...</div>}
      {isError && (
        <div className="banner banner--warn">{backendMessage(error, 'Falha ao carregar notas.')}</div>
      )}

      {!isLoading && !isError && data && data.data.length === 0 && (
        <div className="list-state">Nenhuma nota encontrada.</div>
      )}

      {!isLoading && !isError && data && data.data.length > 0 && (
        <>
          <table className="table">
            <thead>
              <tr>
                <th>Tomador</th>
                <th>Descrição</th>
                <th>Valor</th>
                <th>Status</th>
                <th>Nº NF</th>
                <th>Agendada</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((inv) => (
                <tr key={inv.id}>
                  <td>{inv.client_name || '—'}</td>
                  <td>{inv.description}</td>
                  <td>{formatAmount(inv.amount)}</td>
                  <td>
                    <span className={statusClass(inv.status)}>{STATUS_LABEL[inv.status]}</span>
                  </td>
                  <td>{inv.nf_number ?? '—'}</td>
                  <td>{formatDate(inv.scheduled_date)}</td>
                  <td>
                    <Link to={`/notas/${inv.id}`} className="btn btn-outline">
                      Detalhes
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <span>
              {total} nota(s) — página {page} de {totalPages}
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

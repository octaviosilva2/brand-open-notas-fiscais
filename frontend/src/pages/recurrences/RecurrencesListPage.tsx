/** Listagem de recorrências: tabela com tomador/descrição/valor/dia/início/ativo,
 *  filtros (cliente, ativo), paginação e estados de loading/erro/vazio. */

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useRecurrences } from '../../features/recurrences/hooks';
import { backendMessage } from '../../features/clients/errors';
import type { Recurrence } from '../../features/recurrences/types';

/** Nome do tomador a partir do snapshot `inf_dps.toma.xNome`. */
function tomadorNome(r: Recurrence): string {
  const toma = r.inf_dps?.toma as { xNome?: string } | undefined;
  return toma?.xNome ?? '—';
}

function formatAmount(amount: string): string {
  const n = Number(amount);
  if (!Number.isFinite(n)) return amount;
  return `R$ ${n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

type AtivoFilter = 'todos' | 'ativas' | 'inativas';

export function RecurrencesListPage() {
  const location = useLocation();
  const state = location.state as { created?: boolean; updated?: boolean } | null;
  const justCreated = state?.created ?? false;
  const justUpdated = state?.updated ?? false;

  const [clientId, setClientId] = useState('');
  const [ativo, setAtivo] = useState<AtivoFilter>('todos');
  const [page, setPage] = useState(1);

  const is_active = ativo === 'todos' ? undefined : ativo === 'ativas';
  const { data, isLoading, isError, error } = useRecurrences({
    page,
    client_id: clientId.trim() || undefined,
    is_active,
  });

  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;

  return (
    <>
      <div className="page-head">
        <div className="page-title">Recorrências</div>
        <Link to="/recorrencias/nova" className="btn btn-primary">
          Nova recorrência
        </Link>
      </div>

      {justCreated && (
        <div className="banner banner--info">Recorrência criada com sucesso.</div>
      )}
      {justUpdated && (
        <div className="banner banner--info">Recorrência atualizada com sucesso.</div>
      )}

      <div className="toolbar">
        <input
          className="input toolbar__search"
          placeholder="Filtrar por ID do cliente..."
          value={clientId}
          onChange={(e) => {
            setClientId(e.target.value);
            setPage(1);
          }}
        />
        <select
          className="input"
          value={ativo}
          onChange={(e) => {
            setAtivo(e.target.value as AtivoFilter);
            setPage(1);
          }}
        >
          <option value="todos">Todas</option>
          <option value="ativas">Somente ativas</option>
          <option value="inativas">Somente inativas</option>
        </select>
      </div>

      {isLoading && <div className="list-state">Carregando recorrências...</div>}
      {isError && (
        <div className="banner banner--warn">{backendMessage(error, 'Falha ao carregar recorrências.')}</div>
      )}

      {!isLoading && !isError && data && data.data.length === 0 && (
        <div className="list-state">Nenhuma recorrência encontrada.</div>
      )}

      {!isLoading && !isError && data && data.data.length > 0 && (
        <>
          <table className="table">
            <thead>
              <tr>
                <th>Tomador</th>
                <th>Descrição</th>
                <th>Valor</th>
                <th>Dia</th>
                <th>Início</th>
                <th>Ativa</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((r) => (
                <tr key={r.id}>
                  <td>{tomadorNome(r)}</td>
                  <td>{r.description}</td>
                  <td>{formatAmount(r.amount)}</td>
                  <td>{r.day_of_month}</td>
                  <td>{r.start_date}</td>
                  <td>{r.is_active ? 'Sim' : 'Não'}</td>
                  <td>
                    <Link to={`/recorrencias/${r.id}/editar`} className="btn btn-outline">
                      Editar
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <span>
              {total} recorrência(s) — página {page} de {totalPages}
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

/**
 * Seletor de cliente para o wizard de recorrência. Duas formas de vincular o
 * tomador a um cliente:
 *  - Selecionar um cliente existente (busca debounced, reusa `useClients`).
 *  - Criar um novo cliente inline (`ClientForm` + `useCreateClient`).
 *
 * Em ambos os casos chama `onPick(client)` com o `Client` resultante — o pai
 * (PessoasStep) guarda o `clientId` e pré-preenche o snapshot do tomador.
 */

import { useEffect, useState } from 'react';
import { useClients, useCreateClient } from '../../features/clients/hooks';
import { backendMessage } from '../../features/clients/errors';
import { ClientForm } from '../../features/clients/ClientForm';
import type { Client, ClientCreate } from '../../features/clients/types';
import { Card } from '../primitives';

interface Props {
  selectedClientId: string | null;
  onPick: (client: Client) => void;
  error?: string;
}

export function ClientPicker({ selectedClientId, onPick, error }: Props) {
  const [mode, setMode] = useState<'select' | 'create'>('select');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [selectedName, setSelectedName] = useState<string>('');
  const [serverError, setServerError] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  const { data, isLoading } = useClients({ page: 1, search });
  const create = useCreateClient();

  function pick(c: Client) {
    setSelectedName(`${c.document_type} ${c.document} — ${c.name}`);
    setSearchInput('');
    setSearch('');
    onPick(c);
  }

  async function handleCreate(payload: ClientCreate) {
    setServerError(null);
    try {
      const created = await create.mutateAsync(payload);
      pick(created);
      setMode('select');
    } catch (err) {
      setServerError(backendMessage(err, 'Não foi possível criar o cliente.'));
    }
  }

  return (
    <Card title="Cliente da recorrência">
      <div className="tabs" role="tablist" style={{ marginBottom: 'var(--space-3)' }}>
        <button
          type="button"
          className={`btn ${mode === 'select' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setMode('select')}
        >
          Selecionar existente
        </button>
        <button
          type="button"
          className={`btn ${mode === 'create' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setMode('create')}
        >
          Criar novo
        </button>
      </div>

      {error && <div className="banner banner--warn">{error}</div>}

      {selectedClientId && selectedName && (
        <div className="banner banner--info">Cliente selecionado: {selectedName}</div>
      )}

      {mode === 'select' && (
        <>
          <input
            className="input"
            placeholder="Buscar por nome, documento ou e-mail..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          {isLoading && <div className="list-state">Carregando clientes...</div>}
          {!isLoading && data && data.data.length === 0 && search && (
            <div className="list-state">Nenhum cliente encontrado.</div>
          )}
          {!isLoading && data && data.data.length > 0 && (
            <ul className="picker-list">
              {data.data.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    className={`picker-list__option ${c.id === selectedClientId ? 'selected' : ''}`}
                    onClick={() => pick(c)}
                  >
                    <strong>{c.name}</strong> — {c.document_type} {c.document}
                    {c.email ? ` — ${c.email}` : ''}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {mode === 'create' && (
        <ClientForm
          onSubmit={handleCreate}
          submitting={create.isPending}
          serverError={serverError}
          submitLabel="Criar e vincular cliente"
        />
      )}
    </Card>
  );
}

/** Edição de cliente: carrega o cliente, envia só os campos alterados (PATCH parcial). */

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ClientForm } from '../../features/clients/ClientForm';
import { useClient, useUpdateClient } from '../../features/clients/hooks';
import { backendMessage } from '../../features/clients/errors';
import type { ClientCreate, ClientUpdate } from '../../features/clients/types';

/** Mantém só os campos cujo valor mudou em relação ao original. */
function changedFields(original: Record<string, unknown>, next: ClientCreate): ClientUpdate {
  const patch: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(next)) {
    if (original[key] !== value) patch[key] = value;
  }
  return patch as ClientUpdate;
}

export function ClientEditPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { data: client, isLoading, isError, error } = useClient(id);
  const update = useUpdateClient(id);
  const [serverError, setServerError] = useState<string | null>(null);

  if (isLoading) return <div className="list-state">Carregando cliente...</div>;
  if (isError || !client) {
    return <div className="banner banner--warn">{backendMessage(error, 'Cliente não encontrado.')}</div>;
  }

  async function onSubmit(data: ClientCreate) {
    setServerError(null);
    const patch = changedFields(client as unknown as Record<string, unknown>, data);
    if (Object.keys(patch).length === 0) {
      navigate('/clientes');
      return;
    }
    try {
      await update.mutateAsync(patch);
      navigate('/clientes');
    } catch (err) {
      setServerError(backendMessage(err, 'Não foi possível salvar as alterações.'));
    }
  }

  return (
    <>
      <div className="page-head">
        <div className="page-title">Editar cliente</div>
      </div>
      <ClientForm
        initial={client}
        onSubmit={onSubmit}
        submitting={update.isPending}
        serverError={serverError}
        submitLabel="Salvar alterações"
      />
    </>
  );
}

/** Criação de cliente: ClientForm + useCreateClient; navega para a lista ao sucesso. */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClientForm } from '../../features/clients/ClientForm';
import { useCreateClient } from '../../features/clients/hooks';
import { backendMessage } from '../../features/clients/errors';
import type { ClientCreate } from '../../features/clients/types';

export function ClientCreatePage() {
  const navigate = useNavigate();
  const create = useCreateClient();
  const [serverError, setServerError] = useState<string | null>(null);

  async function onSubmit(data: ClientCreate) {
    setServerError(null);
    try {
      await create.mutateAsync(data);
      navigate('/clientes');
    } catch (err) {
      setServerError(backendMessage(err, 'Não foi possível criar o cliente.'));
    }
  }

  return (
    <>
      <div className="page-head">
        <div className="page-title">Novo cliente</div>
      </div>
      <ClientForm
        onSubmit={onSubmit}
        submitting={create.isPending}
        serverError={serverError}
        submitLabel="Criar cliente"
      />
    </>
  );
}

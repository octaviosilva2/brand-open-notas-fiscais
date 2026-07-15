/** Detalhe de uma nota gerada (log): metadados da emissão, mensagem de erro,
 *  XML enviado/recebido (com download), link do PDF e botão de retry. */

import { useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useInvoice, useRetryInvoice } from '../../features/invoices/hooks';
import { backendMessage } from '../../features/clients/errors';
import { Card } from '../../components/primitives';
import {
  STATUS_LABEL,
  formatAmount,
  formatDate,
  formatDateTime,
  statusClass,
} from '../../features/invoices/format';

/** Dispara o download de um conteúdo de texto como arquivo local. */
function downloadText(filename: string, content: string, mime = 'application/xml') {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function InvoiceDetailPage() {
  const { id = '' } = useParams();
  const { data: inv, isLoading, isError, error } = useInvoice(id);
  const retry = useRetryInvoice(id);

  if (isLoading) return <div className="list-state">Carregando nota...</div>;
  if (isError || !inv) {
    return (
      <div className="banner banner--warn">{backendMessage(error, 'Nota não encontrada.')}</div>
    );
  }

  const canRetry = inv.status === 'error' || inv.status === 'processing';

  return (
    <>
      <div className="page-head">
        <div className="page-title">
          Nota {inv.nf_number ? `nº ${inv.nf_number}` : inv.description}{' '}
          <span className={statusClass(inv.status)}>{STATUS_LABEL[inv.status]}</span>
        </div>
        <Link to="/notas" className="btn btn-outline">
          Voltar
        </Link>
      </div>

      {retry.isSuccess && (
        <div className="banner banner--success">Emissão retentada com sucesso.</div>
      )}
      {retry.isError && (
        <div className="banner banner--warn">
          {backendMessage(retry.error, 'Falha ao retentar a emissão.')}
        </div>
      )}
      {inv.error_message && (
        <div className="banner banner--warn">{inv.error_message}</div>
      )}

      <Card title="Dados da nota">
        <div className="kv">
          <div className="kv__row">
            <span className="kv__k">Tomador</span>
            <span className="kv__v">{inv.client_name || '—'}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Descrição</span>
            <span className="kv__v">{inv.description}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Valor</span>
            <span className="kv__v">{formatAmount(inv.amount)}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Data agendada</span>
            <span className="kv__v">{formatDate(inv.scheduled_date)}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Emissão</span>
            <span className="kv__v">{formatDateTime(inv.emission_date)}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Número da NF</span>
            <span className="kv__v">{inv.nf_number ?? '—'}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Nº DPS</span>
            <span className="kv__v">{inv.n_dps ?? '—'}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Protocolo</span>
            <span className="kv__v">{inv.protocol ?? '—'}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Criada em</span>
            <span className="kv__v">{formatDateTime(inv.created_at)}</span>
          </div>
          <div className="kv__row">
            <span className="kv__k">Atualizada em</span>
            <span className="kv__v">{formatDateTime(inv.updated_at)}</span>
          </div>
        </div>

        <div className="form-actions">
          {inv.pdf_url && (
            <a
              className="btn btn-primary"
              href={inv.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Abrir PDF
            </a>
          )}
          {canRetry && (
            <button
              type="button"
              className="btn btn-outline"
              disabled={retry.isPending}
              onClick={() => retry.mutate()}
            >
              {retry.isPending ? 'Retentando...' : 'Retentar emissão'}
            </button>
          )}
        </div>
      </Card>

      <Card title="XML enviado">
        {inv.xml_sent ? (
          <>
            <div className="row-actions">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => downloadText(`dps_${inv.n_dps ?? inv.id}.xml`, inv.xml_sent!)}
              >
                Baixar XML
              </button>
            </div>
            <pre className="payload-preview">{inv.xml_sent}</pre>
          </>
        ) : (
          <div className="list-state">XML não disponível para esta nota.</div>
        )}
      </Card>

      <Card title="XML de resposta">
        {inv.xml_response ? (
          <>
            <div className="row-actions">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() =>
                  downloadText(`resposta_${inv.n_dps ?? inv.id}.xml`, inv.xml_response!)
                }
              >
                Baixar resposta
              </button>
            </div>
            <pre className="payload-preview">{inv.xml_response}</pre>
          </>
        ) : (
          <div className="list-state">Resposta não disponível para esta nota.</div>
        )}
      </Card>
    </>
  );
}

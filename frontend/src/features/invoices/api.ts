/** Funções de API de invoices/notas contra os endpoints REST do backend.
 *  Notas são geradas pelo cron/recorrências — aqui só há leitura e retry. */

import { api } from '../../api/http';
import type { Invoice, InvoiceDetail, InvoiceListParams, Paginated } from './types';

export function listInvoices(p: InvoiceListParams) {
  const qs = new URLSearchParams();
  if (p.page) qs.set('page', String(p.page));
  if (p.page_size) qs.set('page_size', String(p.page_size));
  if (p.status) qs.set('status', p.status);
  if (p.client_id) qs.set('client_id', p.client_id);
  if (p.from) qs.set('from', p.from);
  if (p.to) qs.set('to', p.to);
  return api<Paginated<Invoice>>(`/invoices?${qs}`);
}

export const getInvoice = (id: string) => api<InvoiceDetail>(`/invoices/${id}`);

/** Retenta a emissão de uma nota com status 'error' ou 'processing' travado. */
export const retryInvoice = (id: string) =>
  api<Invoice>(`/invoices/${id}/retry`, { method: 'POST' });

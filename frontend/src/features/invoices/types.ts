/** Tipos do domínio de invoices/notas (espelham InvoiceRead/Detail do backend). */

export type { Paginated } from '../clients/types';

export type InvoiceStatus = 'pending' | 'processing' | 'success' | 'error';

export interface Invoice {
  id: string;
  recurrence_id: string;
  client_id: string;
  client_name: string;
  scheduled_date: string; // AAAA-MM-DD
  amount: string; // string decimal
  description: string;
  status: InvoiceStatus;
  n_dps: number | null;
  protocol: string | null;
  nf_number: string | null;
  pdf_url: string | null;
  error_message: string | null;
  emission_date: string | null; // ISO datetime
  created_at: string;
  updated_at: string;
}

/** InvoiceRead + XML enviado/recebido — só vem em GET /invoices/{id}. */
export interface InvoiceDetail extends Invoice {
  xml_sent: string | null;
  xml_response: string | null;
}

export interface InvoiceListParams {
  page?: number;
  page_size?: number;
  status?: InvoiceStatus;
  client_id?: string;
  from?: string; // AAAA-MM-DD
  to?: string; // AAAA-MM-DD
}

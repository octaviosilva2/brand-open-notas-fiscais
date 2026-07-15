/** Helpers de apresentação de invoices: rótulo/cor de status e formatações. */

import type { InvoiceStatus } from './types';

export const STATUS_LABEL: Record<InvoiceStatus, string> = {
  pending: 'Pendente',
  processing: 'Processando',
  success: 'Emitida',
  error: 'Erro',
};

/** Classe modificadora do badge de status (ver .badge--* em base.css). */
export const statusClass = (s: InvoiceStatus) => `badge badge--${s}`;

export function formatAmount(amount: string): string {
  const n = Number(amount);
  if (!Number.isFinite(n)) return amount;
  return `R$ ${n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** AAAA-MM-DD → DD/MM/AAAA (sem criar Date para evitar fuso). */
export function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const [y, m, d] = iso.slice(0, 10).split('-');
  return d && m && y ? `${d}/${m}/${y}` : iso;
}

/** ISO datetime → DD/MM/AAAA HH:MM. */
export function formatDateTime(iso: string | null): string {
  if (!iso) return '—';
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return dt.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

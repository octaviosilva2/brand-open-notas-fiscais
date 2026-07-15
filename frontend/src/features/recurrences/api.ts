/** Funções de API de recorrências contra os endpoints REST do backend.
 *  Não há DELETE — desativar via `is_active` (PATCH). */

import { api } from '../../api/http';
import type { Paginated, Recurrence, RecurrenceCreate, RecurrenceUpdate } from './types';

export function listRecurrences(p: { page?: number; client_id?: string; is_active?: boolean }) {
  const qs = new URLSearchParams();
  if (p.page) qs.set('page', String(p.page));
  if (p.client_id) qs.set('client_id', p.client_id);
  if (p.is_active != null) qs.set('is_active', String(p.is_active));
  return api<Paginated<Recurrence>>(`/recurrences?${qs}`);
}

export const getRecurrence = (id: string) => api<Recurrence>(`/recurrences/${id}`);

export const createRecurrence = (data: RecurrenceCreate) =>
  api<Recurrence>('/recurrences', { method: 'POST', body: JSON.stringify(data) });

export const updateRecurrence = (id: string, data: RecurrenceUpdate) =>
  api<Recurrence>(`/recurrences/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

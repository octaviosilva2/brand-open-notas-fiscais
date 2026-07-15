/** Funções de API de clientes contra os endpoints REST do backend. */

import { api } from '../../api/http';
import type { Client, ClientCreate, ClientUpdate, CnpjData, Paginated } from './types';

export function listClients(p: { page?: number; page_size?: number; search?: string }) {
  const qs = new URLSearchParams();
  if (p.page) qs.set('page', String(p.page));
  if (p.page_size) qs.set('page_size', String(p.page_size));
  if (p.search) qs.set('search', p.search);
  return api<Paginated<Client>>(`/clients?${qs}`);
}

export const getClient = (id: string) => api<Client>(`/clients/${id}`);

export const createClient = (data: ClientCreate) =>
  api<Client>('/clients', { method: 'POST', body: JSON.stringify(data) });

export const updateClient = (id: string, data: ClientUpdate) =>
  api<Client>(`/clients/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

export const deleteClient = (id: string) =>
  api<void>(`/clients/${id}`, { method: 'DELETE' });

export const fetchCnpj = (cnpj: string) => api<CnpjData>(`/cnpj/${cnpj}`);

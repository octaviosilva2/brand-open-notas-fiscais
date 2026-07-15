/** Hooks TanStack Query para clientes, com invalidação da lista nas mutações. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as apiClients from './api';

const KEY = ['clients'] as const;

export const useClients = (p: { page: number; search: string }) =>
  useQuery({
    queryKey: [...KEY, p],
    queryFn: () => apiClients.listClients({ page: p.page, search: p.search }),
  });

export const useClient = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => apiClients.getClient(id),
    enabled: !!id,
  });

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: apiClients.createClient,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateClient(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof apiClients.updateClient>[1]) =>
      apiClients.updateClient(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: apiClients.deleteClient,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export const useCnpjData = (cnpj: string) =>
  useQuery({
    queryKey: ['cnpj', cnpj],
    queryFn: () => apiClients.fetchCnpj(cnpj),
    enabled: cnpj.length === 14,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

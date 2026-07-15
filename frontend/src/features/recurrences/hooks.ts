/** Hooks TanStack Query para recorrências, com invalidação da lista nas mutações. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as apiRecurrences from './api';

const KEY = ['recurrences'] as const;

export const useRecurrences = (p: { page: number; client_id?: string; is_active?: boolean }) =>
  useQuery({
    queryKey: [...KEY, p],
    queryFn: () => apiRecurrences.listRecurrences(p),
  });

export const useRecurrence = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => apiRecurrences.getRecurrence(id),
    enabled: !!id,
  });

export function useCreateRecurrence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: apiRecurrences.createRecurrence,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateRecurrence(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof apiRecurrences.updateRecurrence>[1]) =>
      apiRecurrences.updateRecurrence(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

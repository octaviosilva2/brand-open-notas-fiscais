/** Hooks TanStack Query para invoices, com invalidação da lista no retry. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as apiInvoices from './api';
import type { InvoiceListParams } from './types';

const KEY = ['invoices'] as const;

export const useInvoices = (p: InvoiceListParams) =>
  useQuery({
    queryKey: [...KEY, p],
    queryFn: () => apiInvoices.listInvoices(p),
  });

export const useInvoice = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => apiInvoices.getInvoice(id),
    enabled: !!id,
  });

export function useRetryInvoice(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiInvoices.retryInvoice(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

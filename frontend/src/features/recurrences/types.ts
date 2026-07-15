/** Tipos do domínio de recorrências (espelham o backend, pós-Plano 2). */

export type { Paginated } from '../clients/types';

export interface RecurrenceCreate {
  client_id: string;
  description: string; // = inf_dps.serv.cServ.xDescServ
  amount: string; // = inf_dps.valores.vServPrest.vServ (string decimal)
  day_of_month: number; // 1..31
  start_date: string; // AAAA-MM-DD
  end_date?: string | null;
  is_active: boolean;
  inf_dps: Record<string, unknown>; // saída de buildInfDps (sem prest/dCompet/calculados)
}

export interface Recurrence extends Omit<RecurrenceCreate, 'inf_dps'> {
  id: string;
  inf_dps: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type RecurrenceUpdate = Partial<Omit<RecurrenceCreate, 'client_id'>>;

/**
 * Funções de busca de lookups (município IBGE, país ISO, lista de serviço, NBS)
 * contra os endpoints reais do backend (`/lookups/*`, Plano 1).
 *
 * A assinatura `(q: string) => Promise<Option[]>` é mantida para que
 * `useOptions`/`MunicipioSelect` e demais componentes não precisem mudar.
 */

import { api } from './http';

export interface Option {
  value: string;
  label: string;
}

export const searchMunicipios = (q: string): Promise<Option[]> =>
  api<Option[]>(`/lookups/municipios?q=${encodeURIComponent(q)}`);

export const searchPaises = (q: string): Promise<Option[]> =>
  api<Option[]>(`/lookups/paises?q=${encodeURIComponent(q)}`);

export const searchListaServico = (q: string): Promise<Option[]> =>
  api<Option[]>(`/lookups/servicos?q=${encodeURIComponent(q)}`);

export const searchNBS = (q: string): Promise<Option[]> =>
  api<Option[]>(`/lookups/nbs?q=${encodeURIComponent(q)}`);

/** Alias histórico usado pelo `MunicipioSelect` (Plano 4). */
export const searchMunicipiosApi = searchMunicipios;

/** Tabela de alíquotas do Simples Nacional (mock — viria do cadastro/API). */
export interface AliquotaSN {
  pAliq: string;
  anexo: string;
  faixa: string;
  rbt12: string;
}

export const TABELA_ALIQUOTAS_SN: AliquotaSN[] = [
  { pAliq: '2,01', anexo: 'Anexo III', faixa: '1ª', rbt12: 'até R$ 180.000,00' },
  { pAliq: '2,00', anexo: 'Anexo IV', faixa: '1ª', rbt12: 'até R$ 180.000,00' },
  { pAliq: '2,17', anexo: 'Anexo V', faixa: '1ª', rbt12: 'até R$ 180.000,00' },
];

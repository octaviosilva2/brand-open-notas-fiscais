/**
 * Valores derivados/calculados pelo sistema — exibidos somente-leitura e NUNCA
 * incluídos no payload da DPS (ver nota em `campos.md`: base de cálculo, valor
 * ISSQN, total de retenções e valor líquido são calculados pelo sistema/ADN).
 */

import type { Dps } from '../types/dps';

/** Converte string monetária pt-BR ("4.235,00") em número. Vazio = 0. */
export function parseMoney(s: string): number {
  if (!s) return 0;
  const normalized = s.replace(/\./g, '').replace(',', '.').replace(/[^0-9.-]/g, '');
  const n = Number(normalized);
  return Number.isFinite(n) ? n : 0;
}

/** Converte string percentual pt-BR ("2,01") em número. */
export function parsePercent(s: string): number {
  if (!s) return 0;
  const n = Number(s.replace(',', '.').replace(/[^0-9.-]/g, ''));
  return Number.isFinite(n) ? n : 0;
}

/** Formata número como moeda pt-BR sem o símbolo (ex.: 4235 -> "4.235,00"). */
export function formatMoney(n: number): string {
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** Competência (mês/ano) derivada da data da prestação (AAAA-MM-DD). */
export function competenciaFromDCompet(dCompet: string): string {
  if (!dCompet) return '';
  const [ano, mes] = dCompet.split('-');
  if (!ano || !mes) return '';
  const meses = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  const idx = Number(mes) - 1;
  const nome = meses[idx] ?? mes;
  return `${nome}/${ano}`;
}

export interface DerivedValues {
  totalDeducoes: number;
  baseCalculo: number;
  valorISSQN: number;
  totalRetencoes: number;
  valorLiquido: number;
}

/** Calcula os valores derivados a partir do estado do formulário. */
export function computeDerived(dps: Dps): DerivedValues {
  const v = dps.valores;
  const vServ = parseMoney(v.vServ);
  const descIncond = parseMoney(v.vDescIncond);
  const descCond = parseMoney(v.vDescCond);

  let totalDeducoes = 0;
  if (v.dedRedTipo === 'valor') {
    totalDeducoes = parseMoney(v.vDR);
  } else if (v.dedRedTipo === 'percentual') {
    totalDeducoes = (vServ * parsePercent(v.pDR)) / 100;
  } else if (v.dedRedTipo === 'documento') {
    totalDeducoes = v.documentos.reduce((acc, d) => acc + parseMoney(d.vDeducaoReducao), 0);
  }

  const baseCalculo = Math.max(0, vServ - descIncond - totalDeducoes);
  const valorISSQN = (baseCalculo * parsePercent(v.pAliq)) / 100;

  const totalRetencoes =
    parseMoney(v.vRetIRRF) +
    parseMoney(v.vRetCSLL) +
    parseMoney(v.vRetCP) +
    parseMoney(v.piscofins.vPis) +
    parseMoney(v.piscofins.vCofins);

  const valorLiquido = Math.max(0, vServ - descCond - totalRetencoes);

  return { totalDeducoes, baseCalculo, valorISSQN, totalRetencoes, valorLiquido };
}

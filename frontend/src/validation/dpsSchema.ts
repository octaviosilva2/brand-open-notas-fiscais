/**
 * Validação por etapa, derivada das obrigatoriedades de `campos.md`.
 * Cada função retorna um mapa { chaveDoCampo: mensagem }. Chave vazia = sem erro.
 * As chaves batem com as usadas nos componentes (ex.: "toma.end.CEP").
 */

import type { Dps, Pessoa } from '../types/dps';
import type { Errors } from '../state/DpsContext';

const REQ = 'Campo obrigatório';

function validatePessoa(p: Pessoa, prefix: string, errors: Errors): void {
  if (p.tipo === 'brasil') {
    const b = p.brasil;
    if (!b.doc.trim()) errors[`${prefix}.doc`] = REQ;
    if (!b.xNome.trim()) errors[`${prefix}.xNome`] = REQ;
    if (b.informarEndereco) {
      if (!b.end.CEP.trim()) errors[`${prefix}.end.CEP`] = REQ;
      if (!b.end.xLgr.trim()) errors[`${prefix}.end.xLgr`] = REQ;
      if (!b.end.nro.trim()) errors[`${prefix}.end.nro`] = REQ;
      if (!b.end.xBairro.trim()) errors[`${prefix}.end.xBairro`] = REQ;
      if (!b.end.cMun.trim()) errors[`${prefix}.end.cMun`] = REQ;
    }
  } else if (p.tipo === 'exterior') {
    const e = p.exterior;
    if (e.nifMode === 'NIF' && !e.NIF.trim()) errors[`${prefix}.NIF`] = REQ;
    if (e.nifMode === 'cNaoNIF' && !e.cNaoNIF.trim()) errors[`${prefix}.cNaoNIF`] = REQ;
    if (!e.xNome.trim()) errors[`${prefix}.xNome`] = REQ;
    if (e.informarEndereco) {
      if (!e.end.cPais.trim()) errors[`${prefix}.end.cPais`] = REQ;
      if (!e.end.cEndPost.trim()) errors[`${prefix}.end.cEndPost`] = REQ;
      if (!e.end.xCidade.trim()) errors[`${prefix}.end.xCidade`] = REQ;
      if (!e.end.xEstProvReg.trim()) errors[`${prefix}.end.xEstProvReg`] = REQ;
      if (!e.end.xLgr.trim()) errors[`${prefix}.end.xLgr`] = REQ;
      if (!e.end.nro.trim()) errors[`${prefix}.end.nro`] = REQ;
      if (!e.end.xBairro.trim()) errors[`${prefix}.end.xBairro`] = REQ;
    }
  }
}

export function validatePessoas(dps: Dps): Errors {
  // Na recorrência a data da prestação (`dCompet`) não é coletada — o backend a
  // injeta por ocorrência —, então não é validada aqui.
  const errors: Errors = {};
  validatePessoa(dps.toma, 'toma', errors);
  validatePessoa(dps.interm, 'interm', errors); // só valida se != naoInformado
  return errors;
}

export function validateServico(dps: Dps): Errors {
  const errors: Errors = {};
  const s = dps.serv;
  if (s.locPrestTipo === 'municipio' && !s.cLocPrestacao.trim()) errors['serv.cLocPrestacao'] = REQ;
  if (s.locPrestTipo === 'pais' && !s.cPaisPrestacao.trim()) errors['serv.cPaisPrestacao'] = REQ;
  if (!s.tribISSQN.trim()) errors['serv.tribISSQN'] = REQ;
  if (!s.tpRetISSQN.trim()) errors['serv.tpRetISSQN'] = REQ;
  if (!s.cTribNac.trim()) errors['serv.cTribNac'] = REQ;
  if (!s.cNBS.trim()) errors['serv.cNBS'] = REQ;
  if (!s.xDescServ.trim()) errors['serv.xDescServ'] = REQ;

  if (s.detalheAdicional === 'obra' || s.detalheAdicional === 'imovel') {
    if (!s.obra.cobr.trim()) errors['serv.obra.cobr'] = REQ;
  } else if (s.detalheAdicional === 'evento') {
    if (!s.evento.xNome.trim()) errors['serv.evento.xNome'] = REQ;
    if (!s.evento.dataIni.trim()) errors['serv.evento.dataIni'] = REQ;
    if (!s.evento.dataFim.trim()) errors['serv.evento.dataFim'] = REQ;
  }
  return errors;
}

export function validateValores(dps: Dps): Errors {
  const errors: Errors = {};
  const v = dps.valores;
  if (!v.vServ.trim()) errors['valores.vServ'] = REQ;
  // Regime especial de tributação é obrigatório na tela (regEspTrib)
  if (!dps.prest.regEspTrib.trim()) errors['prest.regEspTrib'] = REQ;

  if (v.dedRedTipo === 'percentual' && !v.pDR.trim()) errors['valores.pDR'] = REQ;
  if (v.dedRedTipo === 'valor' && !v.vDR.trim()) errors['valores.vDR'] = REQ;
  if (v.dedRedTipo === 'documento') {
    if (v.documentos.length === 0) {
      errors['valores.documentos'] = 'Adicione ao menos um documento';
    } else {
      v.documentos.forEach((d, i) => {
        if (!d.tpDedRed.trim()) errors[`valores.documentos.${i}.tpDedRed`] = REQ;
        if (!d.dtEmiDoc.trim()) errors[`valores.documentos.${i}.dtEmiDoc`] = REQ;
        if (!d.vDedutivelRedutivel.trim()) errors[`valores.documentos.${i}.vDedutivelRedutivel`] = REQ;
        if (!d.vDeducaoReducao.trim()) errors[`valores.documentos.${i}.vDeducaoReducao`] = REQ;
      });
    }
  }

  // PIS/COFINS: se não for "nenhum", o CST é obrigatório
  if (v.piscofins.situacao !== 'nenhum' && !v.piscofins.CST.trim()) {
    errors['valores.piscofins.CST'] = REQ;
  }
  return errors;
}

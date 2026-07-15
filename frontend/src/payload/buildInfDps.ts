/**
 * Monta o objeto `infDPS` (estrutura do XML da DPS) a partir do estado do
 * formulário. Mapeia 1:1 para o que o backend enviará à Betha — ver `campos.md`.
 *
 * Regras importantes:
 * - Grupos opcionais não preenchidos são OMITIDOS (não vão como vazio).
 * - Campos calculados pelo sistema (base de cálculo, valor ISSQN, valor líquido,
 *   total de retenções) NÃO entram aqui — são responsabilidade do ADN/sistema.
 * - Choices (CE) enviam apenas o ramo escolhido.
 *
 * O retorno é um objeto "solto" (Record): é o snapshot `inf_dps` enviado ao criar
 * uma recorrência. NÃO inclui `prest` nem `dCompet` — o backend os injeta no
 * momento da emissão de cada ocorrência.
 */

import type { Dps, Pessoa, EndNac, EndExt } from '../types/dps';

type Json = Record<string, unknown>;

function clean(obj: Json): Json {
  // remove chaves vazias/undefined e objetos que ficaram vazios
  const out: Json = {};
  for (const [k, val] of Object.entries(obj)) {
    if (val === undefined || val === null || val === '') continue;
    if (typeof val === 'object' && !Array.isArray(val)) {
      const nested = clean(val as Json);
      if (Object.keys(nested).length > 0) out[k] = nested;
    } else {
      out[k] = val;
    }
  }
  return out;
}

function buildEndNac(end: EndNac): Json {
  return {
    endNac: clean({ CEP: end.CEP, cMun: end.cMun }),
    xLgr: end.xLgr, nro: end.nro, xCpl: end.xCpl, xBairro: end.xBairro,
  };
}

function buildEndExt(end: EndExt): Json {
  return {
    endExt: clean({
      cPais: end.cPais, cEndPost: end.cEndPost, xCidade: end.xCidade, xEstProvReg: end.xEstProvReg,
    }),
    xLgr: end.xLgr, nro: end.nro, xCpl: end.xCpl, xBairro: end.xBairro,
  };
}

/** Tomador/Intermediário. Retorna undefined quando "não informado". */
function buildPessoa(p: Pessoa): Json | undefined {
  if (p.tipo === 'naoInformado') return undefined;

  if (p.tipo === 'brasil') {
    const b = p.brasil;
    return clean({
      [b.docType]: b.doc,
      xNome: b.xNome, IM: b.IM, CAEPF: b.CAEPF, fone: b.fone, email: b.email,
      end: b.informarEndereco ? buildEndNac(b.end) : '',
    });
  }

  const e = p.exterior;
  return clean({
    NIF: e.nifMode === 'NIF' ? e.NIF : '',
    cNaoNIF: e.nifMode === 'cNaoNIF' ? e.cNaoNIF : '',
    xNome: e.xNome, fone: e.fone, email: e.email,
    end: e.informarEndereco ? buildEndExt(e.end) : '',
  });
}

export function buildInfDps(dps: Dps): Json {
  const s = dps.serv;
  const v = dps.valores;

  // serv/locPrest (choice município x país)
  const locPrest = s.locPrestTipo === 'municipio'
    ? { cLocPrestacao: s.cLocPrestacao }
    : { cPaisPrestacao: s.cPaisPrestacao };

  // grupo condicional dos detalhes adicionais
  let grupoCond: Json = {};
  if (s.detalheAdicional === 'obra' || s.detalheAdicional === 'imovel') {
    grupoCond = { obra: clean({ cobr: s.obra.cobr, ...buildEndNac(s.obra.end) }) };
  } else if (s.detalheAdicional === 'evento') {
    grupoCond = {
      atvEvento: clean({
        xNome: s.evento.xNome, dataIni: s.evento.dataIni, dataFim: s.evento.dataFim,
        ...buildEndNac(s.evento.end),
      }),
    };
  }

  // valores/vDedRed (choice de modalidade)
  let vDedRed: Json | undefined;
  if (v.dedRedTipo === 'percentual') vDedRed = { pDR: v.pDR };
  else if (v.dedRedTipo === 'valor') vDedRed = { vDR: v.vDR };
  else if (v.dedRedTipo === 'documento') {
    vDedRed = {
      documentos: {
        docDedRed: v.documentos.map((d) => clean({
          tpDedRed: d.tpDedRed,
          xDescOutDed: d.tpDedRed === '99' ? d.xDescOutDed : '',
          dtEmiDoc: d.dtEmiDoc,
          vDedutivelRedutivel: d.vDedutivelRedutivel,
          vDeducaoReducao: d.vDeducaoReducao,
          chNFSe: d.docTipo === 'NFSe' ? d.chNFSe : '',
          chNFe: d.docTipo === 'NFe' ? d.chNFe : '',
          NFSeMun: d.docTipo === 'NFSeMun'
            ? clean({ cMunNFSeMun: d.cMunNFSeMun, nNFSeMun: d.nNFSeMun, cVerifNFSeMun: d.cVerifNFSeMun })
            : '',
          NFNFS: d.docTipo === 'NFNFS'
            ? clean({ nNFS: d.nNFS, modNFS: d.modNFS, serieNFS: d.serieNFS })
            : '',
          nDocFisc: d.docTipo === 'docFiscal' ? d.nDocFisc : '',
          nDoc: d.docTipo === 'docNaoFiscal' ? d.nDoc : '',
        })),
      },
    };
  }

  // tribFed/piscofins (omitido se "nenhum")
  const piscofins = v.piscofins.situacao === 'nenhum'
    ? undefined
    : clean({
        CST: v.piscofins.CST,
        vBCPisCofins: v.piscofins.vBCPisCofins,
        pAliqPis: v.piscofins.pAliqPis,
        pAliqCofins: v.piscofins.pAliqCofins,
        vPis: v.piscofins.vPis,
        vCofins: v.piscofins.vCofins,
        tpRetPisCofins: v.piscofins.tpRetPisCofins,
      });

  // Molde da RECORRÊNCIA: os dados fixos de `prest` (CNPJ, fone, email, opSimpNac,
  // regApTribSN) e `dCompet` NÃO entram no snapshot — o backend os injeta na emissão.
  // `regEspTrib` é armazenado para restaurar o campo ao editar a recorrência.
  const infDPS: Json = {
    tpEmit: dps.tpEmit,
    regEspTrib: dps.prest.regEspTrib,
    toma: buildPessoa(dps.toma),
    interm: buildPessoa(dps.interm),
    serv: clean({
      locPrest,
      cServ: clean({
        cTribNac: s.cTribNac, cTribMun: s.cTribMun, cNBS: s.cNBS,
        cIntContrib: s.cIntContrib, xDescServ: s.xDescServ,
      }),
      ...grupoCond,
      infoCompl: clean({
        idDocTec: s.idDocTec, docRef: s.docRef, xPed: s.xPed,
        gItemPed: s.xItemPed ? { xItemPed: s.xItemPed } : '',
        xInfComp: s.xInfComp,
      }),
    }),
    valores: clean({
      vServPrest: clean({ vServ: v.vServ, vReceb: v.vReceb }),
      vDescCondIncond: clean({ vDescIncond: v.vDescIncond, vDescCond: v.vDescCond }),
      vDedRed: vDedRed ?? '',
      trib: clean({
        tribMun: clean({
          tribISSQN: s.tribISSQN,
          pAliq: v.pAliq,
          tpRetISSQN: s.tpRetISSQN,
          cPaisResult: s.tribISSQN === '3' ? v.cPaisResult : '',
          tpImunidade: s.tribISSQN === '2' ? v.tpImunidade : '',
        }),
        tribFed: clean({
          piscofins: piscofins ?? '',
          vRetCP: v.vRetCP, vRetIRRF: v.vRetIRRF, vRetCSLL: v.vRetCSLL,
        }),
      }),
    }),
  };

  return clean(infDPS);
}

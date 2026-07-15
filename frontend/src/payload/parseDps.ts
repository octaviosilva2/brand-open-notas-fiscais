/**
 * Inverso de buildInfDps: reconstrói o estado Dps do formulário a partir do
 * snapshot inf_dps armazenado na recorrência. Campos ausentes ficam nos
 * defaults de emptyDps(). Campos fixos de prest (CNPJ, fone, etc.) e dCompet
 * não estão no snapshot — o backend os injeta na emissão.
 */

import {
  emptyDps, emptyEndNac, emptyEndExt, emptyPessoa, emptyDocDedRed,
  type Dps, type Pessoa, type EndNac, type EndExt, type DocDedRed,
} from '../types/dps';

type Json = Record<string, unknown>;

function s(v: unknown): string {
  return v == null ? '' : String(v);
}

function obj(v: unknown): Json | undefined {
  return v != null && typeof v === 'object' && !Array.isArray(v) ? (v as Json) : undefined;
}

function parseEndNac(end: Json): EndNac {
  const endNac = obj(end.endNac);
  return {
    ...emptyEndNac(),
    CEP: s(endNac?.CEP),
    cMun: s(endNac?.cMun),
    xLgr: s(end.xLgr),
    nro: s(end.nro),
    xCpl: s(end.xCpl),
    xBairro: s(end.xBairro),
  };
}

function parseEndExt(end: Json): EndExt {
  const endExt = obj(end.endExt);
  return {
    ...emptyEndExt(),
    cPais: s(endExt?.cPais),
    cEndPost: s(endExt?.cEndPost),
    xCidade: s(endExt?.xCidade),
    xEstProvReg: s(endExt?.xEstProvReg),
    xLgr: s(end.xLgr),
    nro: s(end.nro),
    xCpl: s(end.xCpl),
    xBairro: s(end.xBairro),
  };
}

function parsePessoa(data: unknown): Pessoa {
  const base = emptyPessoa();
  const d = obj(data);
  if (!d) return base;

  // Exterior: identificado pela presença de NIF ou cNaoNIF
  if (d.NIF != null || d.cNaoNIF != null) {
    const endData = obj(d.end);
    return {
      tipo: 'exterior',
      brasil: base.brasil,
      exterior: {
        nifMode: d.NIF ? 'NIF' : 'cNaoNIF',
        NIF: s(d.NIF),
        cNaoNIF: s(d.cNaoNIF) || '0',
        xNome: s(d.xNome),
        fone: s(d.fone),
        email: s(d.email),
        informarEndereco: !!endData,
        end: endData ? parseEndExt(endData) : emptyEndExt(),
      },
    };
  }

  // Brasil: CNPJ ou CPF
  const docType = d.CNPJ != null ? 'CNPJ' : 'CPF';
  const endData = obj(d.end);
  return {
    tipo: 'brasil',
    brasil: {
      docType,
      doc: s(docType === 'CNPJ' ? d.CNPJ : d.CPF),
      xNome: s(d.xNome),
      IM: s(d.IM),
      CAEPF: s(d.CAEPF),
      fone: s(d.fone),
      email: s(d.email),
      informarEndereco: !!endData,
      end: endData ? parseEndNac(endData) : emptyEndNac(),
    },
    exterior: base.exterior,
  };
}

function parseDocDedRed(d: unknown): DocDedRed {
  const item = emptyDocDedRed();
  const data = obj(d);
  if (!data) return item;

  item.tpDedRed = s(data.tpDedRed);
  item.xDescOutDed = s(data.xDescOutDed);
  item.dtEmiDoc = s(data.dtEmiDoc);
  item.vDedutivelRedutivel = s(data.vDedutivelRedutivel);
  item.vDeducaoReducao = s(data.vDeducaoReducao);

  if (data.chNFSe) { item.docTipo = 'NFSe'; item.chNFSe = s(data.chNFSe); }
  else if (data.chNFe) { item.docTipo = 'NFe'; item.chNFe = s(data.chNFe); }
  else if (data.NFSeMun) {
    const m = obj(data.NFSeMun);
    item.docTipo = 'NFSeMun';
    item.cMunNFSeMun = s(m?.cMunNFSeMun);
    item.nNFSeMun = s(m?.nNFSeMun);
    item.cVerifNFSeMun = s(m?.cVerifNFSeMun);
  } else if (data.NFNFS) {
    const n = obj(data.NFNFS);
    item.docTipo = 'NFNFS';
    item.nNFS = s(n?.nNFS);
    item.modNFS = s(n?.modNFS);
    item.serieNFS = s(n?.serieNFS);
  } else if (data.nDocFisc) { item.docTipo = 'docFiscal'; item.nDocFisc = s(data.nDocFisc); }
  else if (data.nDoc) { item.docTipo = 'docNaoFiscal'; item.nDoc = s(data.nDoc); }

  return item;
}

export function parseDps(infDps: Record<string, unknown>): Dps {
  const dps = emptyDps();

  dps.tpEmit = s(infDps.tpEmit) || '1';
  dps.prest.regEspTrib = s(infDps.regEspTrib);
  dps.toma = parsePessoa(infDps.toma);
  dps.interm = parsePessoa(infDps.interm);

  // serv
  const serv = obj(infDps.serv);
  if (serv) {
    const locPrest = obj(serv.locPrest);
    if (locPrest?.cLocPrestacao) {
      dps.serv.locPrestTipo = 'municipio';
      dps.serv.cLocPrestacao = s(locPrest.cLocPrestacao);
    } else if (locPrest?.cPaisPrestacao) {
      dps.serv.locPrestTipo = 'pais';
      dps.serv.cPaisPrestacao = s(locPrest.cPaisPrestacao);
    }

    const cServ = obj(serv.cServ);
    if (cServ) {
      dps.serv.cTribNac = s(cServ.cTribNac);
      dps.serv.cTribMun = s(cServ.cTribMun);
      dps.serv.cNBS = s(cServ.cNBS);
      dps.serv.cIntContrib = s(cServ.cIntContrib);
      dps.serv.xDescServ = s(cServ.xDescServ);
    }

    const obra = obj(serv.obra);
    if (obra) {
      dps.serv.detalheAdicional = 'obra';
      dps.serv.obra.cobr = s(obra.cobr);
      dps.serv.obra.end = parseEndNac(obra);
    }

    const atvEvento = obj(serv.atvEvento);
    if (atvEvento) {
      dps.serv.detalheAdicional = 'evento';
      dps.serv.evento.xNome = s(atvEvento.xNome);
      dps.serv.evento.dataIni = s(atvEvento.dataIni);
      dps.serv.evento.dataFim = s(atvEvento.dataFim);
      dps.serv.evento.end = parseEndNac(atvEvento);
    }

    const infoCompl = obj(serv.infoCompl);
    if (infoCompl) {
      dps.serv.idDocTec = s(infoCompl.idDocTec);
      dps.serv.docRef = s(infoCompl.docRef);
      dps.serv.xPed = s(infoCompl.xPed);
      const gItemPed = obj(infoCompl.gItemPed);
      dps.serv.xItemPed = s(gItemPed?.xItemPed);
      dps.serv.xInfComp = s(infoCompl.xInfComp);
    }
  }

  // valores
  const valores = obj(infDps.valores);
  if (valores) {
    const vServPrest = obj(valores.vServPrest);
    dps.valores.vServ = s(vServPrest?.vServ);
    dps.valores.vReceb = s(vServPrest?.vReceb);

    const vDescCondIncond = obj(valores.vDescCondIncond);
    dps.valores.vDescIncond = s(vDescCondIncond?.vDescIncond);
    dps.valores.vDescCond = s(vDescCondIncond?.vDescCond);

    const vDedRed = obj(valores.vDedRed);
    if (vDedRed) {
      if (vDedRed.pDR != null) {
        dps.valores.dedRedTipo = 'percentual';
        dps.valores.pDR = s(vDedRed.pDR);
      } else if (vDedRed.vDR != null) {
        dps.valores.dedRedTipo = 'valor';
        dps.valores.vDR = s(vDedRed.vDR);
      } else if (vDedRed.documentos) {
        dps.valores.dedRedTipo = 'documento';
        const docs = obj(vDedRed.documentos);
        const docDedRed = docs?.docDedRed;
        if (Array.isArray(docDedRed)) {
          dps.valores.documentos = docDedRed.map(parseDocDedRed);
        }
      }
    }

    const trib = obj(valores.trib);
    const tribMun = obj(trib?.tribMun);
    if (tribMun) {
      dps.serv.tribISSQN = s(tribMun.tribISSQN);
      dps.serv.tpRetISSQN = s(tribMun.tpRetISSQN);
      dps.valores.pAliq = s(tribMun.pAliq);
      dps.valores.cPaisResult = s(tribMun.cPaisResult);
      dps.valores.tpImunidade = s(tribMun.tpImunidade);
    }

    const tribFed = obj(trib?.tribFed);
    if (tribFed) {
      dps.valores.vRetCP = s(tribFed.vRetCP);
      dps.valores.vRetIRRF = s(tribFed.vRetIRRF);
      dps.valores.vRetCSLL = s(tribFed.vRetCSLL);

      const piscofins = obj(tribFed.piscofins);
      if (piscofins) {
        dps.valores.piscofins.situacao = 'basica';
        dps.valores.piscofins.CST = s(piscofins.CST);
        dps.valores.piscofins.vBCPisCofins = s(piscofins.vBCPisCofins);
        dps.valores.piscofins.pAliqPis = s(piscofins.pAliqPis);
        dps.valores.piscofins.pAliqCofins = s(piscofins.pAliqCofins);
        dps.valores.piscofins.vPis = s(piscofins.vPis);
        dps.valores.piscofins.vCofins = s(piscofins.vCofins);
        dps.valores.piscofins.tpRetPisCofins = s(piscofins.tpRetPisCofins);
      }
    }
  }

  return dps;
}

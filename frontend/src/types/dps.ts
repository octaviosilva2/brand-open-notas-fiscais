/**
 * Modelo de dados do formulário da DPS (Declaração de Prestação de Serviço),
 * espelhando a árvore `infDPS` do leiaute nacional da NFS-e — ver `campos.md`.
 *
 * Todos os campos de input são `string` (binding direto com <input>); a conversão
 * para os tipos do XML acontece no momento de montar o payload para a API futura.
 * Campos calculados pelo sistema (base de cálculo, valor ISSQN, valor líquido,
 * total de retenções) NÃO ficam aqui — são derivados só para exibição.
 */

// ---------- Endereço ----------

export interface EndNac {
  CEP: string;
  cMun: string; // código IBGE (7)
  xLgr: string;
  nro: string;
  xCpl: string;
  xBairro: string;
}

export interface EndExt {
  cPais: string; // código ISO (2)
  cEndPost: string;
  xCidade: string;
  xEstProvReg: string;
  xLgr: string;
  nro: string;
  xCpl: string;
  xBairro: string;
}

export function emptyEndNac(): EndNac {
  return { CEP: '', cMun: '', xLgr: '', nro: '', xCpl: '', xBairro: '' };
}

export function emptyEndExt(): EndExt {
  return { cPais: '', cEndPost: '', xCidade: '', xEstProvReg: '', xLgr: '', nro: '', xCpl: '', xBairro: '' };
}

// ---------- Pessoa (Tomador / Intermediário) ----------

export type PessoaTipo = 'naoInformado' | 'brasil' | 'exterior';

/** Brasil: identifica por CPF ou CNPJ (choice). */
export interface PessoaBrasil {
  docType: 'CPF' | 'CNPJ';
  doc: string;
  xNome: string;
  IM: string;
  CAEPF: string;
  fone: string;
  email: string;
  informarEndereco: boolean;
  end: EndNac;
}

/** Exterior: NIF ou motivo de não informar NIF (choice). */
export interface PessoaExterior {
  nifMode: 'NIF' | 'cNaoNIF';
  NIF: string;
  cNaoNIF: string; // 0 não informado / 1 dispensado / 2 não exigência
  xNome: string;
  fone: string;
  email: string;
  informarEndereco: boolean;
  end: EndExt;
}

export interface Pessoa {
  tipo: PessoaTipo;
  brasil: PessoaBrasil;
  exterior: PessoaExterior;
}

export function emptyPessoaBrasil(): PessoaBrasil {
  return {
    docType: 'CNPJ', doc: '', xNome: '', IM: '', CAEPF: '', fone: '', email: '',
    informarEndereco: false, end: emptyEndNac(),
  };
}

export function emptyPessoaExterior(): PessoaExterior {
  return {
    nifMode: 'NIF', NIF: '', cNaoNIF: '0', xNome: '', fone: '', email: '',
    informarEndereco: false, end: emptyEndExt(),
  };
}

export function emptyPessoa(): Pessoa {
  return { tipo: 'naoInformado', brasil: emptyPessoaBrasil(), exterior: emptyPessoaExterior() };
}

// ---------- Serviço ----------

export type LocPrestTipo = 'municipio' | 'pais';

export interface Serv {
  locPrestTipo: LocPrestTipo;
  cLocPrestacao: string; // município IBGE (7)
  cPaisPrestacao: string; // país ISO (2)
  // tribMun (XML em valores/trib/tribMun, mas digitados na tela Serviço)
  tribISSQN: string; // Natureza da operação: 1/2/3/4
  tpRetISSQN: string; // 1 não retido / 2 retido tomador / 3 retido interm.
  // cServ
  cTribNac: string; // Lista de Serviço (ex.: 17.01.01 -> 170101)
  cTribMun: string;
  cNBS: string;
  cIntContrib: string;
  xDescServ: string;
  // detalhes adicionais (choice de grupo condicional)
  detalheAdicional: 'naoInformar' | 'obra' | 'imovel' | 'evento';
  obra: ObraInfo;
  evento: EventoInfo;
  // infoCompl
  idDocTec: string;
  docRef: string;
  xPed: string;
  xItemPed: string;
  xInfComp: string;
}

export interface ObraInfo {
  cobr: string; // CNO/CIB
  end: EndNac;
}

export interface EventoInfo {
  xNome: string;
  dataIni: string;
  dataFim: string;
  end: EndNac;
}

export function emptyServ(): Serv {
  return {
    locPrestTipo: 'municipio', cLocPrestacao: '', cPaisPrestacao: '',
    tribISSQN: '', tpRetISSQN: '',
    cTribNac: '', cTribMun: '', cNBS: '', cIntContrib: '', xDescServ: '',
    detalheAdicional: 'naoInformar',
    obra: { cobr: '', end: emptyEndNac() },
    evento: { xNome: '', dataIni: '', dataFim: '', end: emptyEndNac() },
    idDocTec: '', docRef: '', xPed: '', xItemPed: '', xInfComp: '',
  };
}

// ---------- Valores ----------

export type DedRedTipo = 'nenhuma' | 'percentual' | 'valor' | 'documento';

export type DocDedRedDocTipo =
  | 'NFSe' | 'NFe' | 'NFSeMun' | 'NFNFS' | 'docFiscal' | 'docNaoFiscal';

export interface DocDedRed {
  tpDedRed: string; // 01–08, 99
  xDescOutDed: string; // quando tpDedRed = 99
  dtEmiDoc: string;
  vDedutivelRedutivel: string;
  vDeducaoReducao: string;
  docTipo: DocDedRedDocTipo;
  chNFSe: string;
  chNFe: string;
  // NFSeMun
  cMunNFSeMun: string;
  nNFSeMun: string;
  cVerifNFSeMun: string;
  // NFNFS
  nNFS: string;
  modNFS: string;
  serieNFS: string;
  nDocFisc: string;
  nDoc: string;
}

export function emptyDocDedRed(): DocDedRed {
  return {
    tpDedRed: '', xDescOutDed: '', dtEmiDoc: '', vDedutivelRedutivel: '', vDeducaoReducao: '',
    docTipo: 'NFSe', chNFSe: '', chNFe: '',
    cMunNFSeMun: '', nNFSeMun: '', cVerifNFSeMun: '',
    nNFS: '', modNFS: '', serieNFS: '', nDocFisc: '', nDoc: '',
  };
}

export interface PisCofins {
  /** Situação Tributária PIS/COFINS — 'nenhum' = grupo não enviado. */
  situacao: 'nenhum' | 'basica' | 'diferenciada' | 'unidade';
  CST: string;
  vBCPisCofins: string;
  pAliqPis: string;
  pAliqCofins: string;
  vPis: string;
  vCofins: string;
  tpRetPisCofins: string;
}

export interface Valores {
  // vServPrest
  vServ: string;
  vReceb: string;
  // vDescCondIncond
  vDescIncond: string;
  vDescCond: string;
  // vDedRed
  dedRedTipo: DedRedTipo;
  pDR: string;
  vDR: string;
  documentos: DocDedRed[];
  // tribMun (parte que aparece na tela Valores)
  pAliq: string; // alíquota ISSQN
  cPaisResult: string; // exportação (tribISSQN=3)
  tpImunidade: string; // imunidade (tribISSQN=2)
  // tribFed
  piscofins: PisCofins;
  vRetCP: string;
  vRetIRRF: string;
  vRetCSLL: string;
}

export function emptyValores(): Valores {
  return {
    vServ: '', vReceb: '', vDescIncond: '', vDescCond: '',
    dedRedTipo: 'nenhuma', pDR: '', vDR: '', documentos: [],
    pAliq: '', cPaisResult: '', tpImunidade: '',
    piscofins: {
      situacao: 'nenhum', CST: '', vBCPisCofins: '', pAliqPis: '', pAliqCofins: '',
      vPis: '', vCofins: '', tpRetPisCofins: '',
    },
    vRetCP: '', vRetIRRF: '', vRetCSLL: '',
  };
}

// ---------- Prestador (emitente) ----------

export interface Prest {
  // identificação normalmente pré-preenchida pelo cadastro do emitente (mock)
  CNPJ: string;
  xNome: string;
  // regTrib
  opSimpNac: string; // 1 não optante / 2 MEI / 3 ME-EPP
  regApTribSN: string;
  regEspTrib: string; // 0 Nenhum / 1 Ato Cooperado / ...
}

export function emptyPrest(): Prest {
  return { CNPJ: '', xNome: '', opSimpNac: '', regApTribSN: '', regEspTrib: '' };
}

// ---------- DPS (raiz infDPS) ----------

export interface Dps {
  dCompet: string; // data da prestação AAAA-MM-DD
  tpEmit: string; // 1 prestador / 2 tomador / 3 interm.
  toma: Pessoa;
  interm: Pessoa;
  serv: Serv;
  valores: Valores;
  prest: Prest;
}

export function emptyDps(): Dps {
  return {
    dCompet: '', tpEmit: '1',
    toma: emptyPessoa(),
    interm: emptyPessoa(),
    serv: emptyServ(),
    valores: emptyValores(),
    prest: emptyPrest(),
  };
}

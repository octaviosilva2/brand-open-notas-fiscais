# app/integrations/betha/xml_builder.py
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.core.settings import settings
from app.integrations.betha.models import DpsPayload

_NS = "http://www.betha.com.br/e-nota-dps"
_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"

ET.register_namespace("soapenv", _SOAP)
ET.register_namespace("", _NS)


def _n(tag: str) -> str:
    return f"{{{_NS}}}{tag}"


def _s(tag: str) -> str:
    return f"{{{_SOAP}}}{tag}"


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el


def _put(parent: ET.Element, tag: str, value: Any) -> None:
    """Cria o elemento `tag` em `parent` apenas se `value` for não vazio."""
    if value not in (None, ""):
        _sub(parent, _n(tag), str(value))


def _put_decimal(parent: ET.Element, tag: str, value: Any) -> None:
    """Cria elemento numérico normalizando vírgula BR → ponto (padrão XML decimal)."""
    if value not in (None, ""):
        _sub(parent, _n(tag), str(value).replace(",", "."))


def _build_end(parent: ET.Element, end: dict[str, Any] | None) -> None:
    """Monta o grupo `end` (endNac ou endExt + logradouro/número/etc.).

    O front entrega `end` no formato `{endNac|endExt: {...}, xLgr, nro, xCpl,
    xBairro}` — ver `buildInfDps.ts`. A ordem segue o leiaute: o subgrupo de
    localização (endNac/endExt) primeiro, depois logradouro, número, complemento
    e bairro.
    """
    if not end:
        return
    el = _sub(parent, _n("end"))

    end_nac = end.get("endNac")
    end_ext = end.get("endExt")
    if end_nac:
        nac = _sub(el, _n("endNac"))
        # ordem: cMun, CEP (schema exige cMun antes de CEP)
        _put(nac, "cMun", end_nac.get("cMun"))
        _put(nac, "CEP", end_nac.get("CEP"))
    elif end_ext:
        ext = _sub(el, _n("endExt"))
        # ordem: cPais, cEndPost, xCidade, xEstProvReg
        _put(ext, "cPais", end_ext.get("cPais"))
        _put(ext, "cEndPost", end_ext.get("cEndPost"))
        _put(ext, "xCidade", end_ext.get("xCidade"))
        _put(ext, "xEstProvReg", end_ext.get("xEstProvReg"))

    _put(el, "xLgr", end.get("xLgr"))
    _put(el, "nro", end.get("nro"))
    _put(el, "xCpl", end.get("xCpl"))
    _put(el, "xBairro", end.get("xBairro"))


def _build_pessoa(dps_el: ET.Element, tag: str, pessoa: dict[str, Any] | None) -> None:
    """Monta `toma`/`interm` na ordem do leiaute, omitindo o que estiver ausente.

    Ordem: CNPJ|CPF|NIF, cNaoNIF, CAEPF, IM, xNome, end, fone, email.
    """
    if not pessoa:
        return
    el = _sub(dps_el, _n(tag))
    _put(el, "CNPJ", pessoa.get("CNPJ"))
    _put(el, "CPF", pessoa.get("CPF"))
    _put(el, "NIF", pessoa.get("NIF"))
    _put(el, "cNaoNIF", pessoa.get("cNaoNIF"))
    _put(el, "CAEPF", pessoa.get("CAEPF"))
    _put(el, "IM", pessoa.get("IM"))
    _put(el, "xNome", pessoa.get("xNome"))
    _build_end(el, pessoa.get("end"))
    _put(el, "fone", pessoa.get("fone"))
    _put(el, "email", pessoa.get("email"))


def _build_loc_prest(serv_el: ET.Element, loc_prest: dict[str, Any] | None) -> None:
    """Monta `serv/locPrest` (choice município nacional x país)."""
    if not loc_prest:
        return
    el = _sub(serv_el, _n("locPrest"))
    # choice: cLocPrestacao (município) OU cPaisPrestacao (país)
    _put(el, "cLocPrestacao", loc_prest.get("cLocPrestacao"))
    _put(el, "cPaisPrestacao", loc_prest.get("cPaisPrestacao"))


def _build_cserv(serv_el: ET.Element, cserv: dict[str, Any] | None) -> None:
    """Monta `serv/cServ` na ordem do leiaute."""
    if not cserv:
        return
    el = _sub(serv_el, _n("cServ"))
    _put(el, "cTribNac", cserv.get("cTribNac"))
    _put(el, "cTribMun", cserv.get("cTribMun"))
    _put(el, "xDescServ", cserv.get("xDescServ"))
    _put(el, "cNBS", cserv.get("cNBS"))
    _put(el, "cIntContrib", cserv.get("cIntContrib"))


def _build_end_local(parent: ET.Element, end: dict[str, Any] | None) -> None:
    """Monta o endereço de `obra`/`atvEvento` (choice CEP|endExt + logradouro).

    Diferente do `end` de pessoa: aqui o CEP entra direto no grupo, sem endNac.
    Snapshots antigos do front trazem `endNac: {CEP, cMun}` — o CEP é extraído
    e o cMun descartado (não existe no leiaute de obra/evento).
    """
    if not end:
        return
    el = _sub(parent, _n("end"))
    end_nac = end.get("endNac") or {}
    _put(el, "CEP", end.get("CEP") or end_nac.get("CEP"))
    end_ext = end.get("endExt")
    if end_ext:
        ext = _sub(el, _n("endExt"))
        _put(ext, "cPais", end_ext.get("cPais"))
        _put(ext, "cEndPost", end_ext.get("cEndPost"))
        _put(ext, "xCidade", end_ext.get("xCidade"))
        _put(ext, "xEstProvReg", end_ext.get("xEstProvReg"))
    _put(el, "xLgr", end.get("xLgr"))
    _put(el, "nro", end.get("nro"))
    _put(el, "xCpl", end.get("xCpl"))
    _put(el, "xBairro", end.get("xBairro"))


def _local_end_dict(grupo: dict[str, Any]) -> dict[str, Any] | None:
    """Extrai o endereço de `obra`/`atvEvento` aceitando o formato do front.

    O front (buildInfDps.ts) espalha `endNac`/`xLgr`/... direto no grupo em vez
    de aninhar sob `end`.
    """
    if grupo.get("end"):
        end = grupo["end"]
        return end if isinstance(end, dict) else None
    inline = {
        k: grupo[k]
        for k in ("endNac", "endExt", "CEP", "xLgr", "nro", "xCpl", "xBairro")
        if grupo.get(k)
    }
    return inline or None


def _build_obra(serv_el: ET.Element, obra: dict[str, Any] | None) -> None:
    """Grupo condicional `serv/obra` (obras de construção civil).

    Ordem: inscImobFisc, choice(cObra|cCIB), end. Snapshots antigos do front
    usam a chave `cobr` (CNO/CIB) — tratada como cObra.
    """
    if not obra:
        return
    el = _sub(serv_el, _n("obra"))
    _put(el, "inscImobFisc", obra.get("inscImobFisc"))
    _put(el, "cObra", obra.get("cObra") or obra.get("cobr"))
    _put(el, "cCIB", obra.get("cCIB"))
    _build_end_local(el, _local_end_dict(obra))


def _build_atv_evento(serv_el: ET.Element, evento: dict[str, Any] | None) -> None:
    """Grupo condicional `serv/atvEvento` (atividades de evento).

    Ordem: xNome, dtIni, dtFim, choice(idAtvEvt|end). Snapshots antigos do
    front usam `dataIni`/`dataFim` — mapeados para dtIni/dtFim.
    """
    if not evento:
        return
    el = _sub(serv_el, _n("atvEvento"))
    _put(el, "xNome", evento.get("xNome"))
    _put(el, "dtIni", evento.get("dtIni") or evento.get("dataIni"))
    _put(el, "dtFim", evento.get("dtFim") or evento.get("dataFim"))
    _put(el, "idAtvEvt", evento.get("idAtvEvt"))
    _build_end_local(el, _local_end_dict(evento))


def _build_info_compl(serv_el: ET.Element, info: dict[str, Any] | None) -> None:
    """Monta `serv/infoCompl` na ordem do leiaute."""
    if not info:
        return
    el = _sub(serv_el, _n("infoCompl"))
    # ordem do XSD da Betha: idDocTec, docRef, xPed, xInfComp
    # (o XSD não contempla gItemPed — enviar quebraria a validação)
    _put(el, "idDocTec", info.get("idDocTec"))
    _put(el, "docRef", info.get("docRef"))
    _put(el, "xPed", info.get("xPed"))
    _put(el, "xInfComp", info.get("xInfComp"))


def _build_serv(dps_el: ET.Element, serv: dict[str, Any] | None) -> None:
    """Monta o grupo `serv` (obrigatório no leiaute, mas omitido se ausente)."""
    if not serv:
        return
    el = _sub(dps_el, _n("serv"))
    _build_loc_prest(el, serv.get("locPrest"))
    _build_cserv(el, serv.get("cServ"))
    _build_obra(el, serv.get("obra"))
    _build_atv_evento(el, serv.get("atvEvento"))
    _build_info_compl(el, serv.get("infoCompl"))


def _build_doc_ded_red(documentos_el: ET.Element, doc: dict[str, Any]) -> None:
    """Monta `docDedRed`: choice de identificação primeiro, depois os valores."""
    el = _sub(documentos_el, _n("docDedRed"))
    _put(el, "chNFSe", doc.get("chNFSe"))
    _put(el, "chNFe", doc.get("chNFe"))
    nfse_mun = doc.get("NFSeMun")
    if nfse_mun:
        nm = _sub(el, _n("NFSeMun"))
        _put(nm, "cMunNFSeMun", nfse_mun.get("cMunNFSeMun"))
        _put(nm, "nNFSeMun", nfse_mun.get("nNFSeMun"))
        _put(nm, "cVerifNFSeMun", nfse_mun.get("cVerifNFSeMun"))
    nf_nfs = doc.get("NFNFS")
    if nf_nfs:
        nf = _sub(el, _n("NFNFS"))
        _put(nf, "nNFS", nf_nfs.get("nNFS"))
        _put(nf, "modNFS", nf_nfs.get("modNFS"))
        _put(nf, "serieNFS", nf_nfs.get("serieNFS"))
    _put(el, "nDocFisc", doc.get("nDocFisc"))
    _put(el, "nDoc", doc.get("nDoc"))
    _put(el, "tpDedRed", doc.get("tpDedRed"))
    _put(el, "xDescOutDed", doc.get("xDescOutDed"))
    _put(el, "dtEmiDoc", doc.get("dtEmiDoc"))
    _put_decimal(el, "vDedutivelRedutivel", doc.get("vDedutivelRedutivel"))
    _put_decimal(el, "vDeducaoReducao", doc.get("vDeducaoReducao"))
    fornec = doc.get("fornec")
    if fornec:
        _build_pessoa(el, "fornec", fornec)


def _build_v_ded_red(valores_el: ET.Element, v_ded_red: dict[str, Any] | None) -> None:
    """Monta `valores/vDedRed` (choice pDR | vDR | documentos)."""
    if not v_ded_red:
        return
    el = _sub(valores_el, _n("vDedRed"))
    _put_decimal(el, "pDR", v_ded_red.get("pDR"))
    _put_decimal(el, "vDR", v_ded_red.get("vDR"))
    documentos = v_ded_red.get("documentos")
    if documentos and documentos.get("docDedRed"):
        docs_el = _sub(el, _n("documentos"))
        for doc in documentos["docDedRed"]:
            _build_doc_ded_red(docs_el, doc)


def _build_trib_mun(trib_el: ET.Element, trib_mun: dict[str, Any] | None) -> None:
    """Ordem do XSD: tribISSQN, cPaisResult, BM, exigSusp, tpImunidade, pAliq,
    tpRetISSQN."""
    if not trib_mun:
        return
    el = _sub(trib_el, _n("tribMun"))
    _put(el, "tribISSQN", trib_mun.get("tribISSQN"))
    _put(el, "cPaisResult", trib_mun.get("cPaisResult"))
    bm = trib_mun.get("BM")
    if bm:
        bm_el = _sub(el, _n("BM"))
        _put(bm_el, "nBM", bm.get("nBM"))
        _put_decimal(bm_el, "vRedBCBM", bm.get("vRedBCBM"))
        _put_decimal(bm_el, "pRedBCBM", bm.get("pRedBCBM"))
    exig_susp = trib_mun.get("exigSusp")
    if exig_susp:
        es_el = _sub(el, _n("exigSusp"))
        _put(es_el, "tpSusp", exig_susp.get("tpSusp"))
        _put(es_el, "nProcesso", exig_susp.get("nProcesso"))
    _put(el, "tpImunidade", trib_mun.get("tpImunidade"))
    _put_decimal(el, "pAliq", trib_mun.get("pAliq"))
    _put(el, "tpRetISSQN", trib_mun.get("tpRetISSQN"))


def _build_pis_cofins(trib_fed_el: ET.Element, piscofins: dict[str, Any]) -> None:
    el = _sub(trib_fed_el, _n("piscofins"))
    _put(el, "CST", piscofins.get("CST"))
    _put_decimal(el, "vBCPisCofins", piscofins.get("vBCPisCofins"))
    _put_decimal(el, "pAliqPis", piscofins.get("pAliqPis"))
    _put_decimal(el, "pAliqCofins", piscofins.get("pAliqCofins"))
    _put_decimal(el, "vPis", piscofins.get("vPis"))
    _put_decimal(el, "vCofins", piscofins.get("vCofins"))
    _put(el, "tpRetPisCofins", piscofins.get("tpRetPisCofins"))


def _build_trib_fed(trib_el: ET.Element, trib_fed: dict[str, Any] | None) -> None:
    if not trib_fed:
        return
    el = _sub(trib_el, _n("tribFed"))
    piscofins = trib_fed.get("piscofins")
    if piscofins:
        _build_pis_cofins(el, piscofins)
    _put_decimal(el, "vRetCP", trib_fed.get("vRetCP"))
    _put_decimal(el, "vRetIRRF", trib_fed.get("vRetIRRF"))
    _put_decimal(el, "vRetCSLL", trib_fed.get("vRetCSLL"))


def _build_tot_trib(trib_el: ET.Element) -> None:
    """totTrib: percentuais fixos do prestador (constantes de settings).

    Não é coletado no front, por isso permanece vindo de `settings`.
    """
    tot_trib = _sub(trib_el, _n("totTrib"))
    p_tot_trib = _sub(tot_trib, _n("pTotTrib"))
    _sub(p_tot_trib, _n("pTotTribFed"), settings.TOT_TRIB_FED)
    _sub(p_tot_trib, _n("pTotTribEst"), settings.TOT_TRIB_EST)
    _sub(p_tot_trib, _n("pTotTribMun"), settings.TOT_TRIB_MUN)


def _build_valores(dps_el: ET.Element, valores: dict[str, Any] | None) -> None:
    """Monta o grupo `valores` na ordem do leiaute."""
    if not valores:
        return
    el = _sub(dps_el, _n("valores"))

    v_serv_prest = valores.get("vServPrest")
    if v_serv_prest:
        vsp = _sub(el, _n("vServPrest"))
        # ordem do XSD: vReceb (opcional) antes de vServ
        _put_decimal(vsp, "vReceb", v_serv_prest.get("vReceb"))
        _put_decimal(vsp, "vServ", v_serv_prest.get("vServ"))

    v_desc = valores.get("vDescCondIncond")
    if v_desc:
        vd = _sub(el, _n("vDescCondIncond"))
        _put_decimal(vd, "vDescIncond", v_desc.get("vDescIncond"))
        _put_decimal(vd, "vDescCond", v_desc.get("vDescCond"))

    _build_v_ded_red(el, valores.get("vDedRed"))

    trib = valores.get("trib")
    trib_el = _sub(el, _n("trib"))
    if trib:
        _build_trib_mun(trib_el, trib.get("tribMun"))
        _build_trib_fed(trib_el, trib.get("tribFed"))
    # totTrib é sempre enviado (constantes do prestador)
    _build_tot_trib(trib_el)


class DpsXmlBuilder:
    def build(self, payload: DpsPayload) -> str:
        inf_dps: dict[str, Any] = payload.recurrence.inf_dps or {}

        serie_padded = settings.BETHA_SERIE.zfill(5)
        n_dps_padded = str(payload.n_dps).zfill(15)
        tp_emit = inf_dps.get("tpEmit") or "1"
        # id no formato do leiaute: "DPS" + cLocEmi(7) + tipo de inscrição
        # federal(1: 1=CPF, 2=CNPJ) + inscrição(14) + série(5) + nDPS(15)
        # = 45 caracteres. O 8º dígito NÃO é o tpEmit — no exemplo da Betha,
        # tpEmit=1 e o id traz "2" (CNPJ).
        tp_insc = "2" if len(settings.EMITTER_CNPJ) == 14 else "1"
        inscricao = settings.EMITTER_CNPJ.zfill(14)
        inf_dps_id = (
            f"DPS{settings.CITY_CODE}{tp_insc}{inscricao}{serie_padded}{n_dps_padded}"
        )
        # dhEmi exige fuso horário (TZD). Usa horário local de São Paulo com
        # offset (ex.: 2026-06-09T20:00:00-03:00).
        dh_emi = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(
            timespec="seconds"
        )
        d_compet = payload.emission_date.isoformat()

        envelope = ET.Element(_s("Envelope"))
        _sub(envelope, _s("Header"))
        body = _sub(envelope, _s("Body"))
        req = _sub(body, _n("RecepcionarDpsEnvio"))
        xml_dps = ET.SubElement(req, _n("DPS"), attrib={"versao": "1.01"})

        # atributo "id" minúsculo, conforme o XSD da Betha (nfse_dps_v01.xsd)
        dps = ET.SubElement(xml_dps, _n("infDPS"), attrib={"id": inf_dps_id})
        _sub(dps, _n("tpAmb"), settings.BETHA_ENV)
        _sub(dps, _n("dhEmi"), dh_emi)
        _sub(dps, _n("verAplic"), "nota_WS_1.1.0")
        _sub(dps, _n("serie"), settings.BETHA_SERIE)
        # nDPS sem zeros à esquerda na tag (exemplo Betha: <nDPS>1</nDPS>);
        # o padding de 15 dígitos vale apenas dentro do id.
        _sub(dps, _n("nDPS"), str(payload.n_dps))
        _sub(dps, _n("dCompet"), d_compet)
        _sub(dps, _n("tpEmit"), tp_emit)
        _sub(dps, _n("cLocEmi"), settings.CITY_CODE)

        # prest (BRAND OPEN) permanece fixo em settings
        prest = _sub(dps, _n("prest"))
        _sub(prest, _n("CNPJ"), settings.EMITTER_CNPJ)
        if settings.EMITTER_PHONE:
            _sub(prest, _n("fone"), settings.EMITTER_PHONE)
        if settings.EMITTER_EMAIL:
            _sub(prest, _n("email"), settings.EMITTER_EMAIL)
        reg_trib = _sub(prest, _n("regTrib"))
        _sub(reg_trib, _n("opSimpNac"), settings.OP_SIMP_NAC)
        _sub(reg_trib, _n("regApTribSN"), settings.REG_AP_TRIB_SN)
        reg_esp_trib = inf_dps.get("regEspTrib") or settings.REG_ESP_TRIB
        _sub(reg_trib, _n("regEspTrib"), reg_esp_trib)

        # toma/interm/serv/valores montados a partir do snapshot inf_dps
        _build_pessoa(dps, "toma", inf_dps.get("toma"))
        _build_pessoa(dps, "interm", inf_dps.get("interm"))
        _build_serv(dps, inf_dps.get("serv"))
        _build_valores(dps, inf_dps.get("valores"))

        return ET.tostring(envelope, encoding="unicode", xml_declaration=False)

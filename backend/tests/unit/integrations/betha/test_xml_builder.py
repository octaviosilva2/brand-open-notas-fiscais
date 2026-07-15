# tests/unit/integrations/betha/test_xml_builder.py
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from app.integrations.betha.models import DpsPayload
from app.integrations.betha.xml_builder import DpsXmlBuilder
from app.modules.clients.domain.entities import Client
from app.modules.recurrences.domain.entities import Recurrence


def _make_client(document: str = "12345678901") -> Client:
    now = datetime.now(UTC)
    return Client(
        id=uuid.uuid4(),
        document=document,
        name="Empresa Teste",
        municipal_registration=None,
        phone=None,
        email=None,
        zip_code=None,
        street=None,
        number=None,
        complement=None,
        neighborhood=None,
        ibge_city_code=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _make_recurrence(inf_dps: dict[str, Any]) -> Recurrence:
    now = datetime.now(UTC)
    return Recurrence(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        description="Assessoria",
        amount=Decimal("1500.00"),
        day_of_month=15,
        start_date=date(2026, 1, 1),
        end_date=None,
        is_active=True,
        inf_dps=inf_dps,
        created_at=now,
        updated_at=now,
    )


def _build_and_parse(inf_dps: dict[str, Any], n_dps: int = 1) -> ET.Element:
    payload = DpsPayload(
        recurrence_id=uuid.uuid4(),
        client=_make_client(),
        recurrence=_make_recurrence(inf_dps),
        emission_date=date(2026, 6, 15),
        n_dps=n_dps,
    )
    xml_str = DpsXmlBuilder().build(payload)
    return ET.fromstring(xml_str)


def _find(root: ET.Element, *path: str) -> ET.Element | None:
    current = root
    for tag in path:
        found = None
        for el in current.iter(tag):
            found = el
            break
        if found is None:
            return None
        current = found
    return current


_NS = "{http://www.betha.com.br/e-nota-dps}"


def test_xml_contains_cpf_when_inf_dps_toma_cpf() -> None:
    root = _build_and_parse({"toma": {"CPF": "12345678901", "xNome": "X"}})
    toma = root.find(f".//{_NS}toma")
    assert toma is not None
    assert toma.find(f"{_NS}CPF") is not None


def test_xml_contains_cnpj_for_prest_and_toma() -> None:
    root = _build_and_parse({"toma": {"CNPJ": "11222333000181", "xNome": "X"}})
    # prest sempre tem CNPJ (settings) + toma com CNPJ = 2 ocorrências
    cnpj_els = list(root.iter(f"{_NS}CNPJ"))
    assert len(cnpj_els) >= 2


def test_xml_address_omitted_when_no_end() -> None:
    root = _build_and_parse({"toma": {"CNPJ": "11222333000181", "xNome": "X"}})
    assert _find(root, f"{_NS}CEP") is None
    assert _find(root, f"{_NS}end") is None


def test_xml_address_present_when_end_informado() -> None:
    inf = {
        "toma": {
            "CNPJ": "11222333000181",
            "xNome": "X",
            "end": {
                "endNac": {"CEP": "89251000", "cMun": "4204608"},
                "xLgr": "Rua XV",
                "nro": "100",
                "xBairro": "Centro",
            },
        }
    }
    root = _build_and_parse(inf)
    cep = _find(root, f"{_NS}CEP")
    assert cep is not None
    assert cep.text == "89251000"


def test_xml_description_escaped() -> None:
    inf = {
        "serv": {"cServ": {"xDescServ": 'Assessoria <e> "marketing"'}},
    }
    root = _build_and_parse(inf)
    desc_el = _find(root, f"{_NS}xDescServ")
    assert desc_el is not None
    assert desc_el.text is not None
    assert "marketing" in desc_el.text


def test_xml_n_dps_padded_no_id_e_sem_padding_na_tag() -> None:
    payload = DpsPayload(
        recurrence_id=uuid.uuid4(),
        client=_make_client(),
        recurrence=_make_recurrence({}),
        emission_date=date(2026, 6, 15),
        n_dps=42,
    )
    xml_str = DpsXmlBuilder().build(payload)
    # padding de 15 dígitos só dentro do id do infDPS
    assert "000000000000042" in xml_str
    root = ET.fromstring(xml_str)
    n_dps = _find(root, f"{_NS}nDPS")
    # a tag nDPS vai sem zeros à esquerda (exemplo Betha: <nDPS>1</nDPS>)
    assert n_dps is not None and n_dps.text == "42"


def test_xml_header_e_prest_sempre_presentes() -> None:
    root = _build_and_parse({})
    # cabeçalho e prest vêm de settings mesmo com inf_dps vazio
    assert _find(root, f"{_NS}tpAmb") is not None
    assert _find(root, f"{_NS}prest") is not None
    assert _find(root, f"{_NS}cLocEmi") is not None
    # tpEmit default "1"
    tp_emit = _find(root, f"{_NS}tpEmit")
    assert tp_emit is not None and tp_emit.text == "1"


def test_inf_dps_id_formato_leiaute() -> None:
    # "DPS" + cLocEmi(7) + tipoInscrição(1: 2=CNPJ) + CNPJ(14) + série(5)
    # + nDPS(15) = 45 chars
    root = _build_and_parse({"tpEmit": "1"}, n_dps=200)
    inf = root.find(f".//{_NS}infDPS")
    assert inf is not None
    inf_id = inf.get("id")
    assert inf_id is not None
    assert len(inf_id) == 45
    # cLocEmi=4204608, tipoInscrição=2 (CNPJ), CNPJ=11222333000181,
    # série=00900 (zfill 5)
    assert inf_id.startswith("DPS4204608211222333000181")
    assert inf_id.endswith("00900" + "000000000000200")


def test_inf_dps_id_tipo_inscricao_independe_de_tp_emit() -> None:
    # o 8º dígito do id é o tipo de inscrição federal (2=CNPJ), não o tpEmit
    root = _build_and_parse({}, n_dps=1)
    inf = root.find(f".//{_NS}infDPS")
    assert inf is not None
    inf_id = inf.get("id")
    assert inf_id is not None
    assert inf_id.startswith("DPS42046082")


def test_dh_emi_com_offset_de_fuso() -> None:
    root = _build_and_parse({})
    dh_emi = _find(root, f"{_NS}dhEmi")
    assert dh_emi is not None and dh_emi.text is not None
    # exige TZD; horário de São Paulo é -03:00 (ou -02:00 no horário de verão)
    assert dh_emi.text.endswith("-03:00") or dh_emi.text.endswith("-02:00")
    # formato ISO com segundos: 2026-06-09T20:00:00-03:00
    assert "T" in dh_emi.text and len(dh_emi.text) == 25


def test_info_compl_ordem_e_ignora_g_item_ped() -> None:
    inf = {
        "serv": {
            "infoCompl": {
                "idDocTec": "DOC-1",
                "xInfComp": "info final",
                "xPed": "PO-1",
                "gItemPed": {"xItemPed": ["ITEM-01", "ITEM-02"]},
            }
        }
    }
    root = _build_and_parse(inf)
    info = root.find(f".//{_NS}infoCompl")
    assert info is not None
    tags = [el.tag.replace(_NS, "") for el in info]
    # o XSD da Betha só aceita idDocTec, docRef, xPed e xInfComp;
    # gItemPed não é emitido
    assert tags == ["idDocTec", "xPed", "xInfComp"]
    assert list(info.iter(f"{_NS}xItemPed")) == []


def test_obra_snapshot_do_front_normalizado_para_leiaute() -> None:
    # front antigo grava {cobr, endNac espalhado no grupo}; o XML deve sair
    # com cObra e end no formato do leiaute (CEP direto, sem endNac/cMun)
    inf = {
        "serv": {
            "obra": {
                "cobr": "CNO-123",
                "endNac": {"CEP": "89251000", "cMun": "4204608"},
                "xLgr": "Rua B",
                "nro": "20",
                "xBairro": "Centro",
            }
        }
    }
    root = _build_and_parse(inf)
    obra = root.find(f".//{_NS}obra")
    assert obra is not None
    c_obra = obra.find(f"{_NS}cObra")
    assert c_obra is not None and c_obra.text == "CNO-123"
    assert obra.find(f"{_NS}cobr") is None
    end = obra.find(f"{_NS}end")
    assert end is not None
    tags = [el.tag.replace(_NS, "") for el in end]
    assert tags == ["CEP", "xLgr", "nro", "xBairro"]


def test_atv_evento_snapshot_do_front_normalizado_para_leiaute() -> None:
    inf = {
        "serv": {
            "atvEvento": {
                "xNome": "Show",
                "dataIni": "2026-01-01",
                "dataFim": "2026-01-02",
                "endNac": {"CEP": "89251000", "cMun": "4204608"},
                "xLgr": "Rua C",
                "nro": "30",
                "xBairro": "Centro",
            }
        }
    }
    root = _build_and_parse(inf)
    evt = root.find(f".//{_NS}atvEvento")
    assert evt is not None
    tags = [el.tag.replace(_NS, "") for el in evt]
    # dtIni/dtFim conforme o XSD (não dataIni/dataFim)
    assert tags == ["xNome", "dtIni", "dtFim", "end"]
    dt_ini = evt.find(f"{_NS}dtIni")
    assert dt_ini is not None and dt_ini.text == "2026-01-01"


def test_tot_trib_presente_quando_ha_valores() -> None:
    root = _build_and_parse({"valores": {"vServPrest": {"vServ": "100.00"}}})
    # totTrib (constantes do prestador) é montado dentro do grupo valores/trib
    assert _find(root, f"{_NS}totTrib") is not None

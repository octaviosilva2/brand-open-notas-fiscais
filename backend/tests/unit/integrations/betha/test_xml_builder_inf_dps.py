# tests/unit/integrations/betha/test_xml_builder_inf_dps.py
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from app.integrations.betha.models import DpsPayload
from app.integrations.betha.xml_builder import DpsXmlBuilder
from app.modules.clients.domain.entities import Client
from app.modules.recurrences.domain.entities import Recurrence

_NS = "{http://www.betha.com.br/e-nota-dps}"


def _payload_with(inf_dps: dict[str, Any]) -> DpsPayload:
    now = datetime.now(UTC)
    client = Client(
        id=uuid.uuid4(),
        document="12345678000199",
        name="Cliente",
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
    rec = Recurrence(
        id=uuid.uuid4(),
        client_id=client.id,
        description="Serviço",
        amount=Decimal("100.00"),
        day_of_month=15,
        start_date=date(2026, 1, 1),
        end_date=None,
        is_active=True,
        inf_dps=inf_dps,
        created_at=now,
        updated_at=now,
    )
    return DpsPayload(
        recurrence_id=rec.id,
        client=client,
        recurrence=rec,
        emission_date=date(2026, 6, 15),
        n_dps=1,
    )


def _children(el: ET.Element) -> list[str]:
    return [c.tag.replace(_NS, "") for c in el]


def _inf_dps_el(xml: str) -> ET.Element:
    root = ET.fromstring(xml)
    el = root.find(f".//{_NS}infDPS")
    assert el is not None
    return el


_MIN = {
    "toma": {"CNPJ": "12345678000199", "xNome": "Cliente X"},
    "serv": {"cServ": {"xDescServ": "Consultoria"}},
    "valores": {"vServPrest": {"vServ": "100.00"}},
}


def test_builder_omite_campos_ausentes() -> None:
    xml = DpsXmlBuilder().build(_payload_with(_MIN))
    el = _inf_dps_el(xml)
    toma = el.find(f"{_NS}toma")
    assert toma is not None
    # toma não preencheu email/end -> omitidos no grupo toma
    assert toma.find(f"{_NS}email") is None
    assert toma.find(f"{_NS}end") is None
    # interm não foi informado -> grupo inteiro omitido
    assert el.find(f"{_NS}interm") is None
    assert "Cliente X" in xml
    assert "Consultoria" in xml


def test_toma_so_tem_os_campos_preenchidos_na_ordem() -> None:
    inf = {
        "toma": {
            "CNPJ": "12345678000199",
            "xNome": "Cliente X",
            "end": {
                "endNac": {"CEP": "89251000", "cMun": "4208906"},
                "xLgr": "Rua A",
                "nro": "10",
                "xBairro": "Centro",
            },
            "email": "c@x.com",
        }
    }
    el = _inf_dps_el(DpsXmlBuilder().build(_payload_with(inf)))
    toma = el.find(f"{_NS}toma")
    assert toma is not None
    assert _children(toma) == ["CNPJ", "xNome", "end", "email"]
    end = toma.find(f"{_NS}end")
    assert end is not None
    assert _children(end) == ["endNac", "xLgr", "nro", "xBairro"]


def test_ordem_dos_grupos_de_inf_dps() -> None:
    el = _inf_dps_el(DpsXmlBuilder().build(_payload_with(_MIN)))
    children = _children(el)
    # cabeçalho -> prest -> toma -> serv -> valores
    assert children.index("prest") < children.index("toma")
    assert children.index("toma") < children.index("serv")
    assert children.index("serv") < children.index("valores")


def test_valores_completo_com_dedred_e_piscofins() -> None:
    inf = {
        "valores": {
            "vServPrest": {"vServ": "100.00", "vReceb": "100.00"},
            "vDescCondIncond": {"vDescIncond": "5.00"},
            "vDedRed": {"pDR": "10"},
            "trib": {
                "tribMun": {"tribISSQN": "1", "pAliq": "2.01", "tpRetISSQN": "1"},
                "tribFed": {
                    "piscofins": {"CST": "01", "vPis": "1.00", "vCofins": "2.00"}
                },
            },
        }
    }
    el = _inf_dps_el(DpsXmlBuilder().build(_payload_with(inf)))
    valores = el.find(f"{_NS}valores")
    assert valores is not None
    # vServPrest -> vDescCondIncond -> vDedRed -> trib
    assert _children(valores) == [
        "vServPrest",
        "vDescCondIncond",
        "vDedRed",
        "trib",
    ]
    trib = valores.find(f"{_NS}trib")
    assert trib is not None
    # tribMun -> tribFed -> totTrib (totTrib sempre de settings)
    assert _children(trib) == ["tribMun", "tribFed", "totTrib"]
    piscofins = trib.find(f"{_NS}tribFed/{_NS}piscofins")
    assert piscofins is not None
    assert _children(piscofins) == ["CST", "vPis", "vCofins"]


def test_inf_dps_vazio_ainda_gera_xml_valido() -> None:
    xml = DpsXmlBuilder().build(_payload_with({}))
    el = _inf_dps_el(xml)
    # sem toma/serv/valores, mas com cabeçalho + prest + valores? não.
    assert el.find(f"{_NS}toma") is None
    assert el.find(f"{_NS}serv") is None
    assert el.find(f"{_NS}prest") is not None

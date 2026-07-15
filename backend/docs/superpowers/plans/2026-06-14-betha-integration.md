# Integração Betha — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Pré-requisito:** Planos `2026-06-14-clientes-api.md` e `2026-06-14-recorrencias-api.md` devem estar **completos e mergeados**.

**Goal:** Implementar o adaptador de integração com a API SOAP Betha: builder de XML, assinador (stub para homologação), cliente HTTP, contador sequencial `nDPS` e orquestrador de polling.

**Architecture:** Adaptador de saída puro em `app/integrations/betha/` — sem router HTTP, sem camada de domínio própria. Usa as entidades `Client` e `Recurrence` dos módulos existentes. Contador `nDPS` usa lock pessimista no banco para garantir sequencialidade. XML construído via `xml.etree.ElementTree` para escaping correto.

**Tech Stack:** httpx (async), xml.etree.ElementTree, SQLAlchemy 2.0 async, pytest com mock, aioresponses (para testar HTTP).

---

## Estrutura de arquivos

**Criar:**
- `app/integrations/__init__.py` (já existe, verificar)
- `app/integrations/betha/__init__.py`
- `app/integrations/betha/exceptions.py`
- `app/integrations/betha/models.py`
- `app/integrations/betha/counter.py`
- `app/integrations/betha/xml_builder.py`
- `app/integrations/betha/xml_signer.py`
- `app/integrations/betha/client.py`
- `app/integrations/betha/poller.py`
- `tests/unit/integrations/__init__.py`
- `tests/unit/integrations/betha/__init__.py`
- `tests/unit/integrations/betha/test_xml_builder.py`
- `tests/unit/integrations/betha/test_poller.py`
- `tests/unit/integrations/betha/test_counter.py`

**Modificar:**
- `app/core/settings.py` — adicionar variáveis Betha e constantes de emissão
- `migrations/env.py` — importar `EmissionCounterModel`

**Migration:**
- `migrations/versions/<hash>_add_emission_counters.py`

---

### Task 1: Atualizar `settings.py`

**Files:**
- Modify: `app/core/settings.py`

- [ ] **Step 1: Adicionar as novas variáveis à classe `Settings`**

```python
# Adicionar à classe Settings em app/core/settings.py:

# Integração Betha
BETHA_WSDL_URL: str = "https://nota-eletronica.betha.cloud/dps/ws"
BETHA_ENV: str = "2"          # "1" prod, "2" homologação
BETHA_SERIE: str = "900"
BETHA_POLL_INTERVAL_S: int = 5
BETHA_POLL_MAX_ATTEMPTS: int = 12
BETHA_CERT_PATH: str | None = None
BETHA_CERT_PASSWORD: str | None = None

# Constantes do prestador Brand Open
EMITTER_CNPJ: str = "11222333000181"
CITY_CODE: str = "4204608"

# Constantes fixas de tributo (não variam por emissão)
SERVICE_CODE: str = "170101"
NBS_CODE: str = "114011400"
TAX_RATE: str = "2.01"
TRIB_ISSQN: str = "1"
RET_ISSQN: str = "1"
OP_SIMP_NAC: str = "3"
REG_AP_TRIB_SN: str = "2"
REG_ESP_TRIB: str = "0"
```

- [ ] **Step 2: Verificar que a app ainda inicializa (não requer .env adicional)**

```bash
uv run python -c "from app.core.settings import settings; print(settings.EMITTER_CNPJ)"
```

Esperado: `11222333000181`

- [ ] **Step 3: Commit**

```bash
git add app/core/settings.py
git commit -m "feat(betha): adicionar variáveis de configuração ao settings"
```

---

### Task 2: Exceptions e models

**Files:**
- Create: `app/integrations/betha/__init__.py`
- Create: `app/integrations/betha/exceptions.py`
- Create: `app/integrations/betha/models.py`

- [ ] **Step 1: Criar `__init__.py`**

```bash
touch app/integrations/betha/__init__.py
```

- [ ] **Step 2: Escrever `exceptions.py`**

```python
# app/integrations/betha/exceptions.py


class BethaError(Exception):
    """Erro retornado pela API Betha (código de erro no XML de resposta)."""


class BethaTimeoutError(BethaError):
    """Polling esgotou o número máximo de tentativas."""
```

- [ ] **Step 3: Escrever `models.py`**

```python
# app/integrations/betha/models.py
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from app.modules.clients.domain.entities import Client
from app.modules.recurrences.domain.entities import Recurrence


@dataclass(frozen=True)
class DpsPayload:
    recurrence_id: uuid.UUID
    client: Client
    recurrence: Recurrence
    emission_date: date
    n_dps: int


@dataclass(frozen=True)
class PollResult:
    status: Literal["PROCESSADO", "ERRO", "AGUARDANDO"]
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None
    raw_response: str = ""


@dataclass(frozen=True)
class EmissionResult:
    ok: bool
    protocol: str | None = None
    nf_number: str | None = None
    pdf_url: str | None = None
    xml_sent: str = ""
    xml_response: str = ""
    error_message: str | None = None
```

- [ ] **Step 4: Commit**

```bash
git add app/integrations/betha/
git commit -m "feat(betha): exceptions e modelos de dados"
```

---

### Task 3: EmissionCounter — sequência nDPS

**Files:**
- Create: `app/integrations/betha/counter.py`

- [ ] **Step 1: Escrever `counter.py`**

```python
# app/integrations/betha/counter.py
import sqlalchemy as sa
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class EmissionCounterModel(Base):
    __tablename__ = "emission_counters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    serie: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    last_n: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


async def next_n_dps(session: AsyncSession, serie: str) -> int:
    """Retorna o próximo nDPS e incrementa o contador atomicamente."""
    # Garante que a linha existe (upsert idempotente)
    await session.execute(
        insert(EmissionCounterModel)
        .values(serie=serie, last_n=0)
        .on_conflict_do_nothing(index_elements=["serie"])
    )
    await session.flush()

    result = await session.execute(
        sa.select(EmissionCounterModel)
        .where(EmissionCounterModel.serie == serie)
        .with_for_update()
    )
    counter = result.scalar_one()
    counter.last_n += 1
    await session.flush()
    return counter.last_n
```

- [ ] **Step 2: Commit**

```bash
git add app/integrations/betha/counter.py
git commit -m "feat(betha): EmissionCounter com lock pessimista"
```

---

### Task 4: Registrar model do counter no Alembic e criar migration

**Files:**
- Modify: `migrations/env.py`

- [ ] **Step 1: Importar model em `migrations/env.py`**

Adicionar após os outros imports de models:
```python
import app.integrations.betha.counter  # noqa: F401
```

- [ ] **Step 2: Gerar a migration**

```bash
uv run alembic revision --autogenerate -m "add_emission_counters"
```

Verificar no arquivo gerado:
- Tabela `emission_counters` com `id SERIAL`, `serie VARCHAR(5) UNIQUE`, `last_n INTEGER DEFAULT 0`

- [ ] **Step 3: Aplicar**

```bash
uv run alembic upgrade head
```

- [ ] **Step 4: Seed da série padrão**

Adicionar um seed simples para garantir a linha existe em dev/produção. Criar `scripts/seed/emission_counter.py`:

```python
# scripts/seed/emission_counter.py
import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.core.db.session import db
from app.integrations.betha.counter import EmissionCounterModel


async def seed() -> None:
    session_factory = db.create_session
    async with session_factory() as session:
        await session.execute(
            insert(EmissionCounterModel)
            .values(serie="900", last_n=0)
            .on_conflict_do_nothing(index_elements=["serie"])
        )
        await session.commit()
    print("Seed emission_counter concluído.")


if __name__ == "__main__":
    asyncio.run(seed())
```

Rodar: `uv run python -m scripts.seed.emission_counter`

- [ ] **Step 5: Commit**

```bash
git add migrations/env.py migrations/versions/ scripts/seed/emission_counter.py
git commit -m "feat(betha): migration emission_counters e seed"
```

---

### Task 5: DpsXmlBuilder

**Files:**
- Create: `app/integrations/betha/xml_builder.py`

- [ ] **Step 1: Escrever `xml_builder.py`**

```python
# app/integrations/betha/xml_builder.py
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from app.core.settings import settings
from app.integrations.betha.models import DpsPayload

_NS = "http://www.betha.com.br/e-nota-dps"
_SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el


class DpsXmlBuilder:
    def build(self, payload: DpsPayload) -> str:
        serie_padded = settings.BETHA_SERIE.zfill(5)
        n_dps_padded = str(payload.n_dps).zfill(15)
        inf_dps_id = (
            f"DPS{settings.CITY_CODE}{settings.EMITTER_CNPJ}"
            f"{serie_padded}{n_dps_padded}"
        )
        dh_emi = datetime.now(UTC).isoformat(timespec="seconds")
        d_compet = payload.emission_date.isoformat()

        # SOAP envelope
        envelope = ET.Element(
            "soapenv:Envelope",
            attrib={
                "xmlns:soapenv": _SOAP_ENV,
                "xmlns:e": _NS,
            },
        )
        body = _sub(envelope, "soapenv:Body")
        req = _sub(body, "e:RecepcionarDpsEnvio")
        xml_dps = _sub(req, "e:xmlDps")

        # infDPS
        dps = ET.SubElement(
            xml_dps,
            "infDPS",
            attrib={"Id": inf_dps_id, "versao": "1.00"},
        )
        _sub(dps, "tpAmb", settings.BETHA_ENV)
        _sub(dps, "dhEmi", dh_emi)
        _sub(dps, "serie", settings.BETHA_SERIE)
        _sub(dps, "nDPS", n_dps_padded)
        _sub(dps, "dCompet", d_compet)
        _sub(dps, "cLocEmi", settings.CITY_CODE)

        # prest
        prest = _sub(dps, "prest")
        _sub(prest, "CNPJ", settings.EMITTER_CNPJ)
        reg_trib = _sub(prest, "regTrib")
        _sub(reg_trib, "opSimpNac", settings.OP_SIMP_NAC)
        _sub(reg_trib, "regApTribSN", settings.REG_AP_TRIB_SN)
        _sub(reg_trib, "regEspTrib", settings.REG_ESP_TRIB)

        # toma
        client = payload.client
        toma = _sub(dps, "toma")
        if len(client.document) == 14:
            _sub(toma, "CNPJ", client.document)
        else:
            _sub(toma, "CPF", client.document)
        _sub(toma, "xNome", client.name)

        if client.zip_code:
            end = _sub(toma, "end")
            _sub(end, "CEP", client.zip_code)
            if client.street:
                _sub(end, "xLgr", client.street)
            if client.number:
                _sub(end, "nro", client.number)
            if client.complement:
                _sub(end, "xCpl", client.complement)
            if client.neighborhood:
                _sub(end, "xBairro", client.neighborhood)
            if client.ibge_city_code:
                _sub(end, "cMun", client.ibge_city_code)

        if client.phone:
            _sub(toma, "fone", client.phone)
        if client.email:
            _sub(toma, "email", client.email)

        # serv
        serv = _sub(dps, "serv")
        c_serv = _sub(serv, "cServ")
        _sub(c_serv, "cTribNac", settings.SERVICE_CODE)
        _sub(c_serv, "cNBS", settings.NBS_CODE)
        _sub(c_serv, "xDescServ", payload.recurrence.description)
        loc_prest = _sub(serv, "locPrest")
        _sub(loc_prest, "cLocPrestacao", settings.CITY_CODE)

        # valores
        valores = _sub(dps, "valores")
        v_serv_prest = _sub(valores, "vServPrest")
        _sub(v_serv_prest, "vServ", str(payload.recurrence.amount))

        # tribMun
        trib_mun = _sub(dps, "tribMun")
        _sub(trib_mun, "tribISSQN", settings.TRIB_ISSQN)
        _sub(trib_mun, "tpRetISSQN", settings.RET_ISSQN)
        _sub(trib_mun, "pAliq", settings.TAX_RATE)

        return ET.tostring(envelope, encoding="unicode", xml_declaration=False)
```

- [ ] **Step 2: Commit**

```bash
git add app/integrations/betha/xml_builder.py
git commit -m "feat(betha): DpsXmlBuilder"
```

---

### Task 6: Unit tests — DpsXmlBuilder

**Files:**
- Create: `tests/unit/integrations/__init__.py`
- Create: `tests/unit/integrations/betha/__init__.py`
- Create: `tests/unit/integrations/betha/test_xml_builder.py`

- [ ] **Step 1: Escrever os testes**

```python
# tests/unit/integrations/betha/test_xml_builder.py
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from decimal import Decimal

from app.integrations.betha.models import DpsPayload
from app.integrations.betha.xml_builder import DpsXmlBuilder
from app.modules.clients.domain.entities import Client
from app.modules.recurrences.domain.entities import Recurrence


def _make_client(document: str = "12345678901", **kwargs) -> Client:
    now = datetime.now(UTC)
    return Client(
        id=uuid.uuid4(),
        document=document,
        name="Empresa Teste",
        municipal_registration=None,
        phone=None,
        email=None,
        zip_code=kwargs.get("zip_code"),
        street=kwargs.get("street"),
        number=kwargs.get("number"),
        complement=None,
        neighborhood=kwargs.get("neighborhood"),
        ibge_city_code=kwargs.get("ibge_city_code"),
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _make_recurrence(description: str = "Assessoria") -> Recurrence:
    now = datetime.now(UTC)
    return Recurrence(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        description=description,
        amount=Decimal("1500.00"),
        day_of_month=15,
        start_date=date(2026, 1, 1),
        end_date=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _build_and_parse(client: Client, **kwargs) -> ET.Element:
    payload = DpsPayload(
        recurrence_id=uuid.uuid4(),
        client=client,
        recurrence=_make_recurrence(kwargs.get("description", "Assessoria")),
        emission_date=date(2026, 6, 15),
        n_dps=1,
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


def test_xml_contains_cpf_for_cpf_client():
    root = _build_and_parse(_make_client("12345678901"))
    assert _find(root, "CPF") is not None
    assert _find(root, "CNPJ") is None or _find(root, "CNPJ").text == "11222333000181"


def test_xml_contains_cnpj_for_cnpj_client():
    root = _build_and_parse(_make_client("11222333000181"))
    cnpj_els = [el for el in root.iter("CNPJ")]
    # Deve ter dois: prest/CNPJ e toma/CNPJ
    assert len(cnpj_els) >= 2


def test_xml_address_omitted_when_no_zip():
    root = _build_and_parse(_make_client())
    assert _find(root, "CEP") is None


def test_xml_address_present_when_zip():
    client = _make_client(
        zip_code="89251000",
        street="Rua XV",
        number="100",
        neighborhood="Centro",
        ibge_city_code="4204608",
    )
    root = _build_and_parse(client)
    assert _find(root, "CEP") is not None
    assert _find(root, "CEP").text == "89251000"


def test_xml_description_escaped():
    client = _make_client()
    payload = DpsPayload(
        recurrence_id=uuid.uuid4(),
        client=client,
        recurrence=_make_recurrence("Assessoria <e> \"marketing\""),
        emission_date=date(2026, 6, 15),
        n_dps=1,
    )
    xml_str = DpsXmlBuilder().build(payload)
    # ElementTree auto-escapes, so parse back should recover the string
    root = ET.fromstring(xml_str)
    desc_el = _find(root, "xDescServ")
    assert desc_el is not None
    assert "marketing" in desc_el.text


def test_xml_n_dps_zero_padded():
    client = _make_client()
    payload = DpsPayload(
        recurrence_id=uuid.uuid4(),
        client=client,
        recurrence=_make_recurrence(),
        emission_date=date(2026, 6, 15),
        n_dps=42,
    )
    xml_str = DpsXmlBuilder().build(payload)
    assert "000000000000042" in xml_str
```

- [ ] **Step 2: Rodar**

```bash
uv run pytest tests/unit/integrations/betha/test_xml_builder.py -v
```

Esperado: todos passam.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/integrations/
git commit -m "test(betha): unit tests DpsXmlBuilder"
```

---

### Task 7: DpsXmlSigner

**Files:**
- Create: `app/integrations/betha/xml_signer.py`

- [ ] **Step 1: Escrever `xml_signer.py`**

```python
# app/integrations/betha/xml_signer.py
from app.core.settings import settings


class DpsXmlSigner:
    def sign(self, xml: str) -> str:
        """Retorna o XML assinado. Em homologação sem certificado, retorna inalterado."""
        if not settings.BETHA_CERT_PATH:
            return xml
        raise NotImplementedError("Assinatura XML não implementada para produção.")
```

- [ ] **Step 2: Commit**

```bash
git add app/integrations/betha/xml_signer.py
git commit -m "feat(betha): DpsXmlSigner (stub homologação)"
```

---

### Task 8: BethaClient

**Files:**
- Create: `app/integrations/betha/client.py`

- [ ] **Step 1: Escrever `client.py`**

```python
# app/integrations/betha/client.py
import xml.etree.ElementTree as ET

import httpx

from app.core.settings import settings
from app.integrations.betha.exceptions import BethaError
from app.integrations.betha.models import PollResult

_NS = "http://www.betha.com.br/e-nota-dps"


def _build_submit_envelope(xml_dps_content: str) -> str:
    return xml_dps_content  # O builder já gera o envelope completo


def _build_status_envelope(protocol: str) -> str:
    return (
        f'<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        f' xmlns:e="{_NS}">'
        f"<soapenv:Body>"
        f"<e:ConsultarStatusDpsEnvio>"
        f"<e:tpAmb>{settings.BETHA_ENV}</e:tpAmb>"
        f"<e:codigoIbge>{settings.CITY_CODE}</e:codigoIbge>"
        f"<e:cpfCnpjPrestador>{settings.EMITTER_CNPJ}</e:cpfCnpjPrestador>"
        f"<e:protocolo>{protocol}</e:protocolo>"
        f"<e:tipoIntegracao>EMISSAO</e:tipoIntegracao>"
        f"</e:ConsultarStatusDpsEnvio>"
        f"</soapenv:Body>"
        f"</soapenv:Envelope>"
    )


class BethaClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def submit_dps(self, xml_envelope: str) -> str:
        """Envia DPS e retorna o protocolo."""
        resp = await self._http.post(
            settings.BETHA_WSDL_URL,
            content=xml_envelope.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '""',
            },
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        # Procura protocolo na resposta
        protocol_el = root.find(".//{*}protocolo")
        if protocol_el is None or not protocol_el.text:
            # Verifica erro
            error_el = root.find(".//{*}mensagem")
            msg = error_el.text if error_el is not None else resp.text
            raise BethaError(f"Betha não retornou protocolo: {msg}")
        return protocol_el.text

    async def check_status(self, protocol: str) -> PollResult:
        """Consulta status de processamento pelo protocolo."""
        envelope = _build_status_envelope(protocol)
        resp = await self._http.post(
            settings.BETHA_WSDL_URL,
            content=envelope.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '""',
            },
        )
        resp.raise_for_status()
        raw = resp.text
        root = ET.fromstring(raw)

        status_el = root.find(".//{*}situacao")
        status = (status_el.text or "AGUARDANDO").upper() if status_el is not None else "AGUARDANDO"

        if status not in ("PROCESSADO", "ERRO"):
            return PollResult(status="AGUARDANDO", raw_response=raw)

        nf_el = root.find(".//{*}numeroNota")
        pdf_el = root.find(".//{*}urlPdf")
        err_el = root.find(".//{*}mensagemErro")

        return PollResult(
            status=status,  # type: ignore[arg-type]
            nf_number=nf_el.text if nf_el is not None else None,
            pdf_url=pdf_el.text if pdf_el is not None else None,
            error_message=err_el.text if err_el is not None else None,
            raw_response=raw,
        )
```

- [ ] **Step 2: Commit**

```bash
git add app/integrations/betha/client.py
git commit -m "feat(betha): BethaClient SOAP"
```

---

### Task 9: DpsPoller

**Files:**
- Create: `app/integrations/betha/poller.py`

- [ ] **Step 1: Escrever `poller.py`**

```python
# app/integrations/betha/poller.py
import asyncio

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.integrations.betha.client import BethaClient
from app.integrations.betha.counter import next_n_dps
from app.integrations.betha.exceptions import BethaError
from app.integrations.betha.models import DpsPayload, EmissionResult
from app.integrations.betha.xml_builder import DpsXmlBuilder
from app.integrations.betha.xml_signer import DpsXmlSigner


class DpsPoller:
    def __init__(
        self,
        builder: DpsXmlBuilder | None = None,
        signer: DpsXmlSigner | None = None,
        client: BethaClient | None = None,
    ) -> None:
        self._builder = builder or DpsXmlBuilder()
        self._signer = signer or DpsXmlSigner()
        self._client = client

    async def emit_and_poll(
        self,
        payload: DpsPayload,
    ) -> EmissionResult:
        xml = self._builder.build(payload)
        xml = self._signer.sign(xml)

        async with httpx.AsyncClient(timeout=30.0) as http:
            betha = self._client or BethaClient(http)

            try:
                protocol = await betha.submit_dps(xml)
            except BethaError as e:
                return EmissionResult(ok=False, xml_sent=xml, error_message=str(e))
            except Exception as e:
                return EmissionResult(
                    ok=False, xml_sent=xml, error_message=f"Erro inesperado: {e}"
                )

            for _ in range(settings.BETHA_POLL_MAX_ATTEMPTS):
                await asyncio.sleep(settings.BETHA_POLL_INTERVAL_S)
                try:
                    result = await betha.check_status(protocol)
                except Exception as e:
                    return EmissionResult(
                        ok=False,
                        protocol=protocol,
                        xml_sent=xml,
                        error_message=f"Erro no polling: {e}",
                    )

                if result.status == "PROCESSADO":
                    return EmissionResult(
                        ok=True,
                        protocol=protocol,
                        nf_number=result.nf_number,
                        pdf_url=result.pdf_url,
                        xml_sent=xml,
                        xml_response=result.raw_response,
                    )

                if result.status == "ERRO":
                    return EmissionResult(
                        ok=False,
                        protocol=protocol,
                        xml_sent=xml,
                        xml_response=result.raw_response,
                        error_message=result.error_message,
                    )

        return EmissionResult(
            ok=False,
            protocol=protocol,
            xml_sent=xml,
            error_message="Timeout ao aguardar processamento da Betha.",
        )


async def get_next_n_dps(session: AsyncSession) -> int:
    """Conveniência para obter próximo nDPS a partir de uma sessão."""
    return await next_n_dps(session, settings.BETHA_SERIE)
```

- [ ] **Step 2: Commit**

```bash
git add app/integrations/betha/poller.py
git commit -m "feat(betha): DpsPoller"
```

---

### Task 10: Unit tests — DpsPoller e EmissionCounter

**Files:**
- Create: `tests/unit/integrations/betha/test_poller.py`
- Create: `tests/unit/integrations/betha/test_counter.py`

- [ ] **Step 1: Escrever `test_poller.py`**

```python
# tests/unit/integrations/betha/test_poller.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.betha.exceptions import BethaError
from app.integrations.betha.models import DpsPayload, EmissionResult, PollResult
from app.integrations.betha.poller import DpsPoller
from app.modules.clients.domain.entities import Client
from app.modules.recurrences.domain.entities import Recurrence


def _make_payload() -> DpsPayload:
    now = datetime.now(UTC)
    client = Client(
        id=uuid.uuid4(), document="12345678901", name="X",
        municipal_registration=None, phone=None, email=None,
        zip_code=None, street=None, number=None, complement=None,
        neighborhood=None, ibge_city_code=None, is_active=True,
        created_at=now, updated_at=now,
    )
    recurrence = Recurrence(
        id=uuid.uuid4(), client_id=client.id, description="Serv",
        amount=Decimal("100.00"), day_of_month=15,
        start_date=date(2026, 1, 1), end_date=None, is_active=True,
        created_at=now, updated_at=now,
    )
    return DpsPayload(
        recurrence_id=recurrence.id, client=client, recurrence=recurrence,
        emission_date=date(2026, 6, 15), n_dps=1,
    )


async def test_poller_returns_success_on_processado():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(return_value="PROT123")
    mock_client.check_status = AsyncMock(
        return_value=PollResult(
            status="PROCESSADO", nf_number="NF001", pdf_url="http://pdf.url"
        )
    )

    with patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()):
        poller = DpsPoller(client=mock_client)
        result = await poller.emit_and_poll(_make_payload())

    assert result.ok is True
    assert result.nf_number == "NF001"
    assert result.protocol == "PROT123"


async def test_poller_returns_error_on_erro_status():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(return_value="PROT999")
    mock_client.check_status = AsyncMock(
        return_value=PollResult(status="ERRO", error_message="Documento inválido")
    )

    with patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()):
        poller = DpsPoller(client=mock_client)
        result = await poller.emit_and_poll(_make_payload())

    assert result.ok is False
    assert "Documento inválido" in (result.error_message or "")


async def test_poller_timeout_after_max_attempts():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(return_value="PROT777")
    mock_client.check_status = AsyncMock(
        return_value=PollResult(status="AGUARDANDO")
    )

    with patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()):
        with patch("app.integrations.betha.poller.settings") as mock_settings:
            mock_settings.BETHA_POLL_MAX_ATTEMPTS = 3
            mock_settings.BETHA_POLL_INTERVAL_S = 0
            mock_settings.BETHA_CERT_PATH = None
            poller = DpsPoller(client=mock_client)
            result = await poller.emit_and_poll(_make_payload())

    assert result.ok is False
    assert "Timeout" in (result.error_message or "")


async def test_poller_submit_error_returns_emission_result_false():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(side_effect=BethaError("Falha SOAP"))

    with patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()):
        poller = DpsPoller(client=mock_client)
        result = await poller.emit_and_poll(_make_payload())

    assert result.ok is False
    assert "Falha SOAP" in (result.error_message or "")
```

- [ ] **Step 2: Escrever `test_counter.py`** (teste simples sem banco)

```python
# tests/unit/integrations/betha/test_counter.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


async def test_counter_returns_incremented_value():
    """Verifica que next_n_dps retorna last_n+1."""
    counter_model = MagicMock()
    counter_model.last_n = 5

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = counter_model

    session = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)
    session.flush = AsyncMock()

    from app.integrations.betha.counter import next_n_dps

    with patch(
        "app.integrations.betha.counter.insert",
        return_value=MagicMock(on_conflict_do_nothing=lambda **kw: MagicMock()),
    ):
        result = await next_n_dps(session, "900")

    assert result == 6
    assert counter_model.last_n == 6
```

- [ ] **Step 3: Rodar**

```bash
uv run pytest tests/unit/integrations/ -v
```

Esperado: todos passam.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/integrations/
git commit -m "test(betha): unit tests DpsPoller e EmissionCounter"
```

---

## Verificação final

- [ ] Lint: `uv run ruff check app/integrations/betha/ tests/unit/integrations/`
- [ ] Type check: `uv run mypy app/integrations/betha/`
- [ ] Todos os testes: `uv run pytest tests/unit/integrations/ -v`
- [ ] Confirmar que testes pré-existentes ainda passam: `uv run pytest tests/ -v`

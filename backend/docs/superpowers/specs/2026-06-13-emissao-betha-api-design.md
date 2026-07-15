---
name: emissao-betha-api
description: Spec da integração com a API Betha — builder XML, cliente SOAP, polling
metadata:
  type: project
---

# Spec — Integração Betha (API)

## Contexto

Adaptador de integração pura: constrói o XML da DPS, envia via SOAP para a Betha
Sistemas e faz polling do resultado. Não possui router HTTP próprio — é invocado
exclusivamente pelo módulo Agendador.

Depende de: [[clientes-api]], [[recorrencias-api]]
Consumido por: [[agendador-api]]

---

## Endpoint SOAP Betha

| Item | Valor |
|------|-------|
| URL | `https://nota-eletronica.betha.cloud/dps/ws` |
| Protocolo | SOAP 1.1 (`text/xml`) |
| Operação de envio | `RecepcionarDpsEnvio` |
| Operação de consulta | `ConsultarStatusDpsEnvio` |
| Namespace | `http://www.betha.com.br/e-nota-dps` |
| Ambiente homologação | `tpAmb=2` |
| Ambiente produção | `tpAmb=1` |

Implementação via `httpx` (sem zeep) — o envelope SOAP é construído como string,
enviado com `Content-Type: text/xml; charset=utf-8` e `SOAPAction: ""`.

---

## Estrutura de arquivos

```
app/integrations/betha/
  __init__.py
  client.py          # BethaClient — chamadas HTTP SOAP
  xml_builder.py     # DpsXmlBuilder — monta o XML infDPS
  xml_signer.py      # DpsXmlSigner — assina o XML (hook; identidade em homologação)
  poller.py          # DpsPoller — orquestra submit + polling
  counter.py         # EmissionCounter — sequência nDPS em banco
  models.py          # DpsPayload, EmissionResult, PollResult (dataclasses)
  exceptions.py      # BethaError, BethaTimeoutError
```

Não há `domain/`, `application/` nem `adapters/http/` — este é um adaptador de
saída (driven adapter), não um slice de domínio.

---

## Modelos de dados (`models.py`)

```python
@dataclass(frozen=True)
class DpsPayload:
    recurrence_id: UUID
    client: Client          # entidade do módulo clients
    recurrence: Recurrence  # entidade do módulo recurrences
    emission_date: date     # data do dia em que o cron está rodando
    n_dps: int              # número sequencial da DPS

@dataclass(frozen=True)
class PollResult:
    status: Literal["PROCESSADO", "ERRO", "AGUARDANDO"]
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None
    raw_response: str = ""  # XML bruto para log

@dataclass(frozen=True)
class EmissionResult:
    ok: bool
    protocol: str | None = None
    nf_number: str | None = None
    pdf_url: str | None = None
    xml_sent: str = ""       # XML enviado (para log)
    xml_response: str = ""   # resposta bruta (para log)
    error_message: str | None = None
```

---

## `EmissionCounter` — sequência `nDPS`

Tabela `emission_counters`:

```sql
CREATE TABLE emission_counters (
    id      SERIAL PRIMARY KEY,
    serie   VARCHAR(5) NOT NULL UNIQUE,
    last_n  INTEGER NOT NULL DEFAULT 0
);
```

Operação de incremento (atômica, com lock pessimista):

```python
async def next_n_dps(session: AsyncSession, serie: str) -> int:
    """Retorna o próximo nDPS e incrementa o contador."""
    result = await session.execute(
        select(EmissionCounterModel)
        .where(EmissionCounterModel.serie == serie)
        .with_for_update()
    )
    counter = result.scalar_one()
    counter.last_n += 1
    return counter.last_n
```

`serie` é configurada via `BETHA_SERIE` (default `"900"`).

---

## `DpsXmlBuilder` — construção do XML

Constrói o envelope SOAP completo como string. Não usa bibliotecas de template —
usa `xml.etree.ElementTree` para garantir escaping correto de caracteres especiais
na descrição do serviço.

### Campos variáveis por emissão

| Tag XML | Fonte |
|---------|-------|
| `tpAmb` | `settings.BETHA_ENV` |
| `dhEmi` | `datetime.now(UTC).isoformat(timespec="seconds")` |
| `serie` | `settings.BETHA_SERIE` |
| `nDPS` | `payload.n_dps` (zero-padded a 15 dígitos) |
| `dCompet` | `payload.emission_date.isoformat()` |
| `cLocEmi` | `settings.CITY_CODE` (`"4204608"`) |
| `prest/CNPJ` | `settings.EMITTER_CNPJ` |
| `infDPS id` | `"DPS" + cLocEmi + EMITTER_CNPJ + serie_padded + nDPS_padded` |
| `toma/CNPJ` ou `toma/CPF` | `client.document` (14 dígitos → CNPJ; 11 → CPF) |
| `toma/xNome` | `client.name` |
| `toma/end/*` | `client.zip_code, street, number...` (omitido se sem endereço) |
| `toma/fone` | `client.phone` (omitido se `None`) |
| `toma/email` | `client.email` (omitido se `None`) |
| `serv/cServ/xDescServ` | `recurrence.description` |
| `valores/vServPrest/vServ` | `str(recurrence.amount)` |

### Campos constantes (de `settings`)

`cTribNac=170101`, `cNBS=114011400`, `cLocPrestacao=4204608`, `pAliq=2.01`,
`tribISSQN=1`, `tpRetISSQN=1`, `opSimpNac=3`, `regApTribSN=2`, `regEspTrib=0`,
`tpEmit=1`, `indTotTrib=0` (não informa totais aproximados).

### Grupos omitidos

`interm` (intermediário não informado), `vDescCondIncond`, `vDedRed`, `tribFed`
(PIS/COFINS = Nenhum), `infoCompl`.

---

## `DpsXmlSigner` — assinatura digital

```python
class DpsXmlSigner:
    def sign(self, xml: str) -> str:
        """Retorna o XML assinado. Em homologação, retorna o XML inalterado."""
        if not settings.BETHA_CERT_PATH:
            return xml  # homologação sem certificado
        # produção: assinar com lxml + xmlsec1 (a implementar)
        raise NotImplementedError("Assinatura XML ainda não implementada.")
```

⚠️ **A ser validado:** verificar se homologação aceita envios sem assinatura antes
de implementar `signxml`/`xmlsec1`. Configurar `BETHA_CERT_PATH` vazio para
homologação.

---

## `BethaClient` — chamadas SOAP

```python
class BethaClient:
    def __init__(self, http: httpx.AsyncClient): ...

    async def submit_dps(self, xml_envelope: str) -> str:
        """Envia DPS e retorna o protocolo."""

    async def check_status(
        self,
        protocol: str,
        ibge_code: str,
        prestador_cnpj: str,
    ) -> PollResult:
        """Consulta status de processamento pelo protocolo."""
```

### `submit_dps`

POST para `settings.BETHA_WSDL_URL` com o envelope `RecepcionarDpsEnvio`.
Parseia a resposta XML e extrai o protocolo. Lança `BethaError` se a resposta
contiver código de erro.

### `check_status`

POST com o envelope `ConsultarStatusDpsEnvio`:
```xml
<e:ConsultarStatusDpsEnvio>
  <e:tpAmb>{tpAmb}</e:tpAmb>
  <e:codigoIbge>{CITY_CODE}</e:codigoIbge>
  <e:cpfCnpjPrestador>{EMITTER_CNPJ}</e:cpfCnpjPrestador>
  <e:protocolo>{protocol}</e:protocolo>
  <e:tipoIntegracao>EMISSAO</e:tipoIntegracao>
</e:ConsultarStatusDpsEnvio>
```

Parseia resposta e mapeia para `PollResult`. Status finais: `PROCESSADO` e `ERRO`.
Qualquer outro valor é tratado como `AGUARDANDO`.

---

## `DpsPoller` — orquestração

```python
class DpsPoller:
    async def emit_and_poll(
        self,
        payload: DpsPayload,
        session: AsyncSession,
    ) -> EmissionResult:
        xml = self.builder.build(payload)
        xml = self.signer.sign(xml)

        try:
            protocol = await self.client.submit_dps(xml)
        except BethaError as e:
            return EmissionResult(ok=False, xml_sent=xml, error_message=str(e))

        for attempt in range(settings.BETHA_POLL_MAX_ATTEMPTS):
            await asyncio.sleep(settings.BETHA_POLL_INTERVAL_S)
            result = await self.client.check_status(protocol, ...)

            if result.status == "PROCESSADO":
                return EmissionResult(ok=True, protocol=protocol,
                    nf_number=result.nf_number, pdf_url=result.pdf_url,
                    xml_sent=xml, xml_response=result.raw_response)

            if result.status == "ERRO":
                return EmissionResult(ok=False, protocol=protocol,
                    xml_sent=xml, xml_response=result.raw_response,
                    error_message=result.error_message)

        return EmissionResult(
            ok=False, protocol=protocol, xml_sent=xml,
            error_message="Timeout ao aguardar processamento da Betha."
        )
```

---

## Configurações (`settings.py`)

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `BETHA_WSDL_URL` | `str` | `https://nota-eletronica.betha.cloud/dps/ws` | Endpoint SOAP |
| `BETHA_ENV` | `str` | `"2"` | `"1"` prod, `"2"` homologação |
| `BETHA_SERIE` | `str` | `"900"` | Série da DPS |
| `BETHA_POLL_INTERVAL_S` | `int` | `5` | Segundos entre polls |
| `BETHA_POLL_MAX_ATTEMPTS` | `int` | `12` | Máx tentativas (≈ 1 min) |
| `BETHA_CERT_PATH` | `str \| None` | `None` | Caminho do certificado A1 |
| `BETHA_CERT_PASSWORD` | `str \| None` | `None` | Senha do certificado |
| `EMITTER_CNPJ` | `str` | — | CNPJ do prestador (Brand Open) |
| `CITY_CODE` | `str` | `"4204608"` | Código IBGE Jaraguá do Sul |

---

## Testes

### Unitários (`tests/unit/integrations/betha/`)

- `DpsXmlBuilder`: XML gerado contém todos os campos esperados; endereço omitido
  quando cliente sem endereço; CPF vs CNPJ no `toma` correto.
- `EmissionCounter`: incremento sequencial; unicidade sob concorrência (mock de lock).
- `DpsPoller`: retorno em `PROCESSADO` na 1ª tentativa; retorno em `ERRO`; timeout
  após N tentativas; erro no `submit_dps` retorna `EmissionResult(ok=False)`.

### Integração (`tests/integration/integrations/betha/`)

- Teste de ponta a ponta contra homologação Betha (`tpAmb=2`) — marcado com
  `@pytest.mark.integration_betha` e habilitado via variável de ambiente
  `RUN_BETHA_TESTS=1`. Não roda no CI padrão.
- Validar: submit retorna protocolo válido; polling retorna status final.

---

## Exceções

```python
class BethaError(Exception):
    """Erro retornado pela API Betha (código de erro no XML de resposta)."""

class BethaTimeoutError(BethaError):
    """Polling esgotou o número máximo de tentativas."""
```

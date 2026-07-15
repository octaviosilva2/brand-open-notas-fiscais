# Recorrência como molde de DPS — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans para implementar este plano task-by-task. Os steps usam checkbox (`- [x]`).

**Ordem de execução:** Plano **2 de 5**. Pode ser feito em paralelo com o Plano 1. **Pré-requisito do Plano 5** (frontend de recorrências), que envia o `inf_dps` consumido aqui.

**Goal:** Transformar a recorrência de um registro simples (descrição + valor) num **molde de DPS completo + agendamento**. A recorrência ganha uma coluna `inf_dps` (JSONB) que guarda toda a árvore `infDPS` preenchida no front (toma, interm, serv, valores, deduções, tributos), e o `xml_builder` da Betha passa a montar o XML **a partir desse `inf_dps`**, omitindo o que não foi preenchido. O `prest` (BRAND OPEN) continua fixo em `settings`; campos calculados não são enviados.

**Architecture:**
- **Relação cliente↔recorrência = link + snapshot**: a recorrência mantém `client_id` (registro reutilizável de cliente) **e** grava o snapshot do tomador dentro de `inf_dps.toma`. Editar o cliente depois não altera recorrências já criadas. A emissão usa **sempre** o snapshot em `inf_dps`.
- **Contrato `inf_dps`**: dicionário com a mesma forma que `frontend/src/payload/buildInfDps.ts` produz, **sem** `prest` (fixo em settings) e **sem** `dCompet`/cabeçalho (injetados na emissão). Validado por um modelo Pydantic `InfDps` (campos majoritariamente opcionais) e persistido via `model_dump(exclude_none=True)` — assim "o que não foi preenchido não é gravado nem enviado".
- **`xml_builder` reescrito** com construtores por grupo (`_build_toma`, `_build_interm`, `_build_serv`, `_build_valores`) que respeitam a **ordem do leiaute** (ver `docs/.../campos.md`) e omitem chaves ausentes. Cabeçalho (`tpAmb`, `dhEmi`, `serie`, `nDPS`, `dCompet`, `cLocEmi`, id) e `prest` continuam vindo de settings/emissão.

**Tech Stack:** SQLAlchemy 2.0 async (JSONB), Alembic, Pydantic, `xml.etree.ElementTree`, pytest.

---

## Estrutura de arquivos

**Modificar:**
- `app/modules/recurrences/domain/entities.py` — adicionar `inf_dps: dict` em `Recurrence`, `NewRecurrence`, `UpdateRecurrence` e `to_dict`.
- `app/modules/recurrences/adapters/db/models.py` — coluna `inf_dps` (JSONB).
- `app/modules/recurrences/adapters/db/repository.py` — mapear `inf_dps` em `_to_entity` e nas escritas.
- `app/modules/recurrences/adapters/db/factories.py` — se monta entidades a partir do model (mapear o campo).
- `app/modules/recurrences/adapters/http/schemas.py` — `RecurrenceCreate/Update/Read` com `inf_dps`.
- `app/modules/recurrences/application/dtos/commands.py` — comandos com `inf_dps`.
- `app/integrations/betha/xml_builder.py` — reescrita para ler de `recurrence.inf_dps`.
- `app/core/settings.py` — `SERVICE_CODE`/`NBS_CODE`/`TAX_RATE`/`TRIB_ISSQN`/`RET_ISSQN` deixam de ser usados na emissão (manter como fallback opcional ou remover; ver Task 6).
- `migrations/env.py` — sem mudança (model já importado), confirmar.

**Criar:**
- `app/modules/recurrences/domain/inf_dps.py` — modelo Pydantic `InfDps` (contrato compartilhado).
- `migrations/versions/<hash>_add_inf_dps_to_recurrences.py`.
- `tests/unit/integrations/betha/test_xml_builder_inf_dps.py`.
- Ampliar `tests/integration/modules/recurrences/test_recurrences.py`.

---

### Task 1: Contrato `InfDps` (Pydantic)

**Files:**
- Create: `app/modules/recurrences/domain/inf_dps.py`

Espelha a saída de `buildInfDps.ts`. Todos os grupos são opcionais; a omissão é controlada por `exclude_none=True` na hora de serializar para JSONB.

- [x] **Step 1:** definir os submodelos e o `InfDps`. Esqueleto (completar com os campos de `types/dps.ts`):

```python
# app/modules/recurrences/domain/inf_dps.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EndNac(_Base):
    CEP: str | None = None
    cMun: str | None = None
    xLgr: str | None = None
    nro: str | None = None
    xCpl: str | None = None
    xBairro: str | None = None


class EndExt(_Base):
    cPais: str | None = None
    cEndPost: str | None = None
    xCidade: str | None = None
    xEstProvReg: str | None = None
    xLgr: str | None = None
    nro: str | None = None
    xCpl: str | None = None
    xBairro: str | None = None


class Pessoa(_Base):
    # choice de documento já resolvido pelo front (só o ramo escolhido vem)
    CNPJ: str | None = None
    CPF: str | None = None
    NIF: str | None = None
    cNaoNIF: str | None = None
    xNome: str | None = None
    IM: str | None = None
    CAEPF: str | None = None
    fone: str | None = None
    email: str | None = None
    end: dict | None = None  # endNac/endExt já montado pelo front


class CServ(_Base):
    cTribNac: str | None = None
    cTribMun: str | None = None
    cNBS: str | None = None
    cIntContrib: str | None = None
    xDescServ: str | None = None


class Serv(_Base):
    locPrest: dict | None = None         # {cLocPrestacao} ou {cPaisPrestacao}
    cServ: CServ | None = None
    obra: dict | None = None
    atvEvento: dict | None = None
    infoCompl: dict | None = None


class Valores(_Base):
    vServPrest: dict | None = None
    vDescCondIncond: dict | None = None
    vDedRed: dict | None = None
    trib: dict | None = None             # tribMun/tribFed


class InfDps(_Base):
    tpEmit: str | None = None            # default "1" aplicado na emissão se ausente
    toma: Pessoa | None = None
    interm: Pessoa | None = None
    serv: Serv | None = None
    valores: Valores | None = None
```

> **Decisão de granularidade:** grupos muito ramificados (`end`, `obra`, `infoCompl`, `trib`) ficam como `dict` para evitar reescrever toda a árvore agora; o `xml_builder` lê deles por chave. Se quiser validação mais forte depois, troque os `dict` por submodelos. O importante é `extra="forbid"` nos níveis tipados para pegar typo.

- [x] **Step 2: Commit**

```bash
git add app/modules/recurrences/domain/inf_dps.py
git commit -m "feat(recurrences): contrato Pydantic InfDps (molde de DPS)"
```

---

### Task 2: Domínio — entidade e comandos

**Files:**
- Modify: `app/modules/recurrences/domain/entities.py`
- Modify: `app/modules/recurrences/application/dtos/commands.py`

- [x] **Step 1:** em `entities.py`, adicionar `inf_dps: dict[str, Any]` a `Recurrence`, `NewRecurrence` e `to_dict`; em `UpdateRecurrence`, `inf_dps: dict[str, Any] | Unset = UNSET`.

```python
# NewRecurrence: adicionar após is_active
inf_dps: dict[str, Any]

# UpdateRecurrence: adicionar
inf_dps: dict[str, Any] | Unset = UNSET

# Recurrence: adicionar campo e incluir em to_dict()
inf_dps: dict[str, Any]
# to_dict(): "inf_dps": self.inf_dps,
```

- [x] **Step 2:** refletir nos commands de `application/dtos/commands.py` (`CreateRecurrenceCommand`, `UpdateRecurrenceCommand`) se eles não derivam direto das entidades — adicionar `inf_dps`.

- [x] **Step 3:** rodar mypy no módulo para achar todos os pontos que quebram (construções de `Recurrence`/`NewRecurrence`).

```bash
uv run mypy app/modules/recurrences
```

- [x] **Step 4: Commit**

```bash
git add app/modules/recurrences/domain app/modules/recurrences/application/dtos
git commit -m "feat(recurrences): inf_dps no domínio e commands"
```

---

### Task 3: Persistência — model, migration, repository

**Files:**
- Modify: `app/modules/recurrences/adapters/db/models.py`
- Modify: `app/modules/recurrences/adapters/db/repository.py` (e `factories.py` se aplicável)
- Create: `migrations/versions/<hash>_add_inf_dps_to_recurrences.py`

- [x] **Step 1:** coluna no model:

```python
from sqlalchemy.dialects.postgresql import JSONB
# ...
inf_dps: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
```

- [x] **Step 2:** gerar a migration e revisar o autogenerate (deve ser só `add_column`):

```bash
uv run alembic revision --autogenerate -m "add inf_dps to recurrences"
```

Conferir que a migration faz `op.add_column("recurrences", sa.Column("inf_dps", postgresql.JSONB(...), server_default=sa.text("'{}'::jsonb"), nullable=False))` e o `downgrade` dropa a coluna.

- [x] **Step 3:** mapear `inf_dps` em `_to_entity` do repository e nas escritas (create/update). O `BaseRepository` provavelmente já copia campos por nome — confirmar que `inf_dps` entra no `model → entidade` e `command → model`.

- [x] **Step 4:** aplicar a migration no banco de dev/teste e validar round-trip.

```bash
uv run alembic upgrade head
```

- [x] **Step 5: Commit**

```bash
git add app/modules/recurrences/adapters/db migrations/versions
git commit -m "feat(recurrences): coluna inf_dps (JSONB) e migration"
```

---

### Task 4: HTTP — schemas Create/Update/Read

**Files:**
- Modify: `app/modules/recurrences/adapters/http/schemas.py`

- [x] **Step 1:** `RecurrenceCreate` e `RecurrenceUpdate` recebem `inf_dps: InfDps`. No router, serializar com omissão antes de mandar pro command:

```python
# schemas.py
from app.modules.recurrences.domain.inf_dps import InfDps

class RecurrenceCreate(BaseModel):
    client_id: uuid.UUID
    description: Annotated[str, Field(max_length=1000, min_length=1)]
    amount: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    day_of_month: Annotated[int, Field(ge=1, le=31)]
    start_date: date
    end_date: date | None = None
    is_active: bool = True
    inf_dps: InfDps
    # validate_end_date mantém

class RecurrenceUpdate(BaseModel):
    # ... campos atuais opcionais ...
    inf_dps: InfDps | None = None

class RecurrenceRead(BaseModel):
    # ... campos atuais ...
    inf_dps: dict
    model_config = {"from_attributes": True}
```

- [x] **Step 2:** no router (`create_recurrence`/`update_recurrence`), passar `inf_dps=data.inf_dps.model_dump(exclude_none=True)` ao command, garantindo que campos não preenchidos não sejam gravados. Ex.:

```python
payload = data.model_dump(exclude_unset=True)
if "inf_dps" in payload:
    payload["inf_dps"] = data.inf_dps.model_dump(exclude_none=True)
rec = await creator.create(CreateRecurrenceCommand(**payload))
```

- [x] **Step 3:** rodar a app e validar o schema no OpenAPI (POST /recurrences deve exigir `inf_dps`).

- [x] **Step 4: Commit**

```bash
git add app/modules/recurrences/adapters/http
git commit -m "feat(recurrences): inf_dps nos schemas HTTP create/update/read"
```

---

### Task 5: Reescrita do `xml_builder` para ler de `inf_dps`

**Files:**
- Modify: `app/integrations/betha/xml_builder.py`

**Risco principal:** a **ordem dos elementos** no XML do leiaute é significativa. Não fazer walk genérico do dict — usar construtores explícitos por grupo, na ordem de `campos.md`, lendo cada chave de `inf_dps` e **omitindo quando ausente**.

- [x] **Step 1:** manter o cabeçalho e o `prest` como hoje (de `settings`/emissão). `dCompet = payload.emission_date`. `tpEmit = inf_dps.get("tpEmit", "1")`.

- [x] **Step 2:** substituir os blocos `toma`/`serv`/`valores` chumbados por construtores que leem de `inf_dps`. Helper de omissão:

```python
def _put(parent, tag, value):
    if value not in (None, ""):
        _sub(parent, _n(tag), str(value))

def _build_toma(dps_el, toma: dict | None):
    if not toma:
        return
    el = _sub(dps_el, _n("toma"))
    # ordem: CNPJ|CPF|NIF, cNaoNIF, IM, CAEPF, xNome, end, fone, email
    _put(el, "CNPJ", toma.get("CNPJ"))
    _put(el, "CPF", toma.get("CPF"))
    _put(el, "NIF", toma.get("NIF"))
    _put(el, "cNaoNIF", toma.get("cNaoNIF"))
    _put(el, "IM", toma.get("IM"))
    _put(el, "CAEPF", toma.get("CAEPF"))
    _put(el, "xNome", toma.get("xNome"))
    _build_end(el, toma.get("end"))
    _put(el, "fone", toma.get("fone"))
    _put(el, "email", toma.get("email"))
```

`_build_end` trata `endNac` (com `cMun`/`CEP`) e `endExt` (com `cPais`...). `_build_serv` monta `locPrest` (choice), `cServ` (lendo `cTribNac`/`cNBS`/`xDescServ` **do inf_dps**, não mais de settings), grupos condicionais (`obra`/`atvEvento`) e `infoCompl`. `_build_valores` monta `vServPrest`, `vDescCondIncond`, `vDedRed` (choice pDR/vDR/documentos), `trib/tribMun` e `trib/tribFed/piscofins` lendo de `inf_dps.valores`.

- [x] **Step 3:** `totTrib` (pTotTribFed/Est/Mun) — decidir: continua de settings (constante do prestador) **ou** vem do inf_dps. Manter de settings por ora (não é coletado no front). Documentar no código.

- [x] **Step 4:** o builder passa a ler `payload.recurrence.inf_dps`; `payload.client` deixa de ser usado para toma (o snapshot manda). Pode manter `client` no `DpsPayload` para logging, mas não usá-lo na árvore.

- [x] **Step 5:** validar com um inf_dps de exemplo que o XML sai bem-formado e na ordem certa, comparando com o XML do commit `f8a8996` (fix da estrutura DPS) para os campos equivalentes.

- [x] **Step 6: Commit**

```bash
git add app/integrations/betha/xml_builder.py
git commit -m "feat(betha): montar DPS a partir de recurrence.inf_dps, omitindo vazios"
```

---

### Task 6: Limpeza de settings e cron

**Files:**
- Modify: `app/core/settings.py`
- Verify: `app/modules/cron/application/use_cases/cron_runner.py`

- [x] **Step 1:** `SERVICE_CODE`, `NBS_CODE`, `TAX_RATE`, `TRIB_ISSQN`, `RET_ISSQN` não são mais usados na emissão. Removê-los **ou** marcá-los como deprecated (comentário). `totTrib` e `prest` (CNPJ, regime) **permanecem**. Rodar grep para garantir que nada mais os referencia:

```bash
rg "SERVICE_CODE|NBS_CODE|TAX_RATE|TRIB_ISSQN|RET_ISSQN" app
```

- [x] **Step 2:** o `cron_runner` monta `DpsPayload(recurrence=..., client=...)` — confirmar que segue funcionando (o builder agora lê `recurrence.inf_dps`). Sem mudança esperada além de garantir que `recurrence.inf_dps` chega populado.

- [x] **Step 3: Commit**

```bash
git add app/core/settings.py
git commit -m "refactor(betha): aposentar constantes de serviço/tributo fixas em settings"
```

---

### Task 7: Testes

**Files:**
- Create: `tests/unit/integrations/betha/test_xml_builder_inf_dps.py`
- Modify: `tests/integration/modules/recurrences/test_recurrences.py`
- Verify: `tests/unit/integrations/betha/test_xml_builder.py` (atualizar/aposentar asserts que liam de settings)

- [x] **Step 1: unit do builder** — fixtures com `inf_dps` mínimo (só `toma.CNPJ`/`xNome`, `serv.cServ.xDescServ`, `valores.vServPrest.vServ`) e completo (com endereço, dedução, piscofins). Asserts: campos presentes aparecem; campos ausentes **não** aparecem; ordem dos filhos de `toma`/`serv`/`valores` confere.

```python
def test_builder_omite_campos_ausentes():
    inf = {"toma": {"CNPJ": "12345678000199", "xNome": "Cliente X"},
           "serv": {"cServ": {"xDescServ": "Consultoria"}},
           "valores": {"vServPrest": {"vServ": "100.00"}}}
    xml = DpsXmlBuilder().build(_payload_with(inf))
    assert "<email>" not in xml and "<end>" not in xml
    assert "Cliente X" in xml and "Consultoria" in xml
```

- [x] **Step 2: integração** — criar recorrência com `inf_dps`, ler de volta (`GET`) e conferir que o `inf_dps` voltou sem as chaves None; update parcial do `inf_dps`.

- [x] **Step 3:** suíte + lint + types.

```bash
uv run pytest tests/unit/integrations/betha tests/integration/modules/recurrences
uv run ruff check . && uv run mypy app
```

- [x] **Step 4: Commit**

```bash
git add tests
git commit -m "test(recurrences,betha): inf_dps no fluxo e omissão no XML"
```

---

## Checklist de conclusão

- [x] `recurrences.inf_dps` (JSONB) persistido e retornado, com omissão de campos vazios.
- [x] `POST/PATCH /recurrences` aceitam e validam `inf_dps` (modelo `InfDps`).
- [x] `xml_builder` monta toda a árvore `toma/interm/serv/valores` a partir de `inf_dps`, na ordem do leiaute, omitindo ausentes; `prest`/cabeçalho/`totTrib` fixos.
- [x] Constantes de serviço/tributo aposentadas de `settings`.
- [x] `ruff`, `mypy`, `pytest` verdes; XML conferido contra o leiaute.

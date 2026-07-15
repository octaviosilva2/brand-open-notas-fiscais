# Brand Open — Automated NFS-e Invoicing

> Built as freelance work with [Kauan](https://github.com/KauanHK), published here as a
> portfolio snapshot (no production history/secrets, and the emitter's tax ID was
> replaced with a placeholder — see the security notes below).

[🇺🇸 English](#english) · [🇧🇷 Português](#português)

---

## English

### What it is

Automates the monthly issuance of Brazilian electronic service invoices (NFS-e) for
**Brand Open**, replacing a ~2-hour/month manual process with an integration against the
**Betha Sistemas** SOAP web service (used by many Brazilian municipalities to receive
NFS-e), driven from a small web UI.

### Problem it addresses

Issuing NFS-e manually every month meant logging into the city's portal, filling out the
same recurring fields, and no easy way to review/audit what had been sent. This service
builds the fiscal XML (`DPS`), signs it with a digital certificate (A1, PKCS12), submits
it to Betha's web service, and tracks status — with recurring invoice templates so
month-to-month issuance is mostly "confirm and send."

### Architecture

- **Backend**: Python 3.14, FastAPI (async), SQLAlchemy 2.0 async, PostgreSQL, Alembic.
  Hexagonal architecture per module (`auth`, `clients`, `cnpj`, `cron`, `invoices`,
  `recurrences`, `users`). The Betha integration (`app/integrations/betha/`) builds the
  `infDPS` XML, signs it with XMLDSig using a PKCS12 certificate loaded from a path in
  env (never committed), and calls the SOAP endpoint.
- **Frontend**: React 19, TypeScript, Vite, react-query, react-router — a wizard for
  filling out invoice data.
- **Infra**: Docker Compose (nginx + api + frontend + Postgres + a cron container for
  scheduled/recurring issuance). The original repo also had a CI/CD workflow deploying to
  the client's VPS, removed from this snapshot since it targeted live production
  infrastructure.

### Case study — how AI was used

- **Context** — a real accounting/fiscal workflow with a strict external contract (the
  Betha SOAP API and the municipality's XML schema) — little room for "close enough,"
  since a malformed `infDPS` is rejected by the city.
- **AI-Workflow** — built with Claude Code from a written scope doc (`docs/escopo.md`)
  and incremental specs/plans per feature (auth, recurring invoices, the cron scheduler,
  the Betha integration itself) before implementation — each spec pinned down exact
  field mappings and XML structure ahead of writing code, given how unforgiving the
  external contract is.
- **Architecture** — certificate handling kept out of application code entirely (loaded
  from an env-configured path at runtime) specifically so the fiscal-signing logic could
  be unit-tested without ever touching a real certificate.
- **Evidence** — full XML build + sign + submit pipeline implemented and unit-tested
  against the Betha schema; recurring-invoice and cron-scheduling modules built on top of
  the same auth/client foundation.

### Running it

```bash
# Backend (from backend/)
uv sync
uv run uvicorn app.main:app --reload
uv run pytest

# Frontend (from frontend/)
npm install
npm run dev

# Full stack
docker compose up --build
```

### Security notes

This snapshot was published without the original commit history, and the emitter's real
CNPJ (Brazilian tax ID) — which was hardcoded as a default value in `settings.py` and in
several tests/docs — was replaced with `11.222.333/0001-81`, a well-known placeholder
CNPJ used throughout Brazilian dev documentation. No digital certificate, private key, or
`.env` file was ever committed to the original repository — the certificate is always
loaded from an external path at runtime, by design.

---

## Português

### O que é

Automatiza a emissão mensal de Notas Fiscais de Serviço Eletrônicas (NFS-e) para a
**Brand Open**, substituindo um processo manual de ~2h/mês por uma integração com o
web service SOAP da **Betha Sistemas** (usado por diversas prefeituras brasileiras para
receber NFS-e), operada por uma interface web simples.

### Problema que resolve

Emitir NFS-e manualmente todo mês significava entrar no portal da prefeitura, preencher
os mesmos campos recorrentes, e nenhuma forma fácil de revisar/auditar o que foi enviado.
Este serviço monta o XML fiscal (`DPS`), assina com certificado digital (A1, PKCS12),
envia ao web service da Betha, e acompanha o status — com templates de nota recorrente
para que a emissão mês a mês seja, na prática, "conferir e enviar".

### Arquitetura

- **Backend**: Python 3.14, FastAPI (async), SQLAlchemy 2.0 async, PostgreSQL, Alembic.
  Arquitetura hexagonal por módulo (`auth`, `clients`, `cnpj`, `cron`, `invoices`,
  `recurrences`, `users`). A integração Betha (`app/integrations/betha/`) monta o XML
  `infDPS`, assina com XMLDSig usando um certificado PKCS12 carregado de um caminho via
  env (nunca commitado), e chama o endpoint SOAP.
- **Frontend**: React 19, TypeScript, Vite, react-query, react-router — um wizard para
  preencher os dados da nota.
- **Infra**: Docker Compose (nginx + api + frontend + Postgres + um container cron para
  emissão agendada/recorrente). O repositório original também tinha um workflow de
  CI/CD fazendo deploy na VPS do cliente, removido deste snapshot por apontar para
  infraestrutura de produção real.

### Case study — como a IA foi usada

- **Context** — um fluxo fiscal/contábil real com contrato externo rígido (a API SOAP da
  Betha e o schema XML da prefeitura) — pouco espaço para "quase certo", já que um
  `infDPS` malformado é rejeitado pela prefeitura.
- **AI-Workflow** — construído com Claude Code a partir de um documento de escopo por
  escrito (`docs/escopo.md`) e specs/planos incrementais por feature (auth, notas
  recorrentes, o agendador cron, a própria integração Betha) antes da implementação —
  cada spec fixava o mapeamento exato de campos e a estrutura XML antes de escrever
  código, dado o quão rígido é o contrato externo.
- **Architecture** — o tratamento do certificado ficou inteiramente fora do código de
  aplicação (carregado de um caminho configurado via env em runtime) especificamente
  para que a lógica de assinatura fiscal pudesse ser testada sem nunca tocar num
  certificado real.
- **Evidence** — pipeline completo de montar XML + assinar + enviar implementado e
  testado unitariamente contra o schema da Betha; os módulos de nota recorrente e
  agendamento cron construídos sobre a mesma base de auth/clientes.

### Como rodar

```bash
# Backend (a partir de backend/)
uv sync
uv run uvicorn app.main:app --reload
uv run pytest

# Frontend (a partir de frontend/)
npm install
npm run dev

# Stack completa
docker compose up --build
```

### Notas de segurança

Este snapshot foi publicado sem o histórico de commits original, e o CNPJ real do
emitente — que estava hardcoded como valor-padrão em `settings.py` e em vários
testes/docs — foi substituído por `11.222.333/0001-81`, um CNPJ de exemplo amplamente
conhecido e usado em documentação de desenvolvimento no Brasil. Nenhum certificado
digital, chave privada ou arquivo `.env` jamais foi commitado no repositório original —
o certificado sempre é carregado de um caminho externo em runtime, por desenho.

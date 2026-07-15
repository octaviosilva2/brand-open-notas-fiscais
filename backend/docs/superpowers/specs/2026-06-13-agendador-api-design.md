---
name: agendador-api
description: Spec do módulo agendador — endpoint POST /cron/run, lógica do job e notificação por e-mail
metadata:
  type: project
---

# Spec — Módulo Agendador (API)

## Contexto

Módulo responsável por disparar as emissões de NFS-e: tanto via cron diário (chamada
automática do Docker) quanto via botão manual na interface. Implementa a regra de
idempotência (não reprocessar sucesso do dia) e envia e-mail de resumo ao final.

Depende de: [[recorrencias-api]], [[notas-fiscais-api]], [[emissao-betha-api]]

---

## Endpoint

```
POST /cron/run
```

### Autenticação

Aceita **qualquer um** dos dois mecanismos:

| Mecanismo | Usado por |
|-----------|-----------|
| `Authorization: Bearer {JWT}` | Botão manual na interface (sessão da responsável) |
| `X-Cron-Secret: {CRON_SECRET}` | Cron do Docker Compose |

Se nenhum dos dois for válido → `401 Unauthorized`.

### Response

```json
{
  "date": "2026-06-13",
  "total": 5,
  "success": 4,
  "error": 1,
  "results": [
    {
      "recurrence_id": "...",
      "client_name": "Brand Open",
      "invoice_id": "...",
      "ok": true,
      "nf_number": "123456",
      "pdf_url": "https://..."
    },
    {
      "recurrence_id": "...",
      "client_name": "Empresa X",
      "invoice_id": "...",
      "ok": false,
      "error_message": "Timeout ao aguardar processamento da Betha."
    }
  ]
}
```

O endpoint retorna `200` mesmo que haja falhas individuais — o campo `error` indica
quantas falharam. Um erro geral (ex: banco indisponível) retorna `500`.

---

## Lógica do job (`CronRunner`)

```
app/modules/cron/
  application/
    use_cases/
      cron_runner.py     # CronRunner
  adapters/
    http/
      router.py          # POST /cron/run
      schemas.py         # CronResult, CronItemResult
      dependencies.py    # validate_cron_auth (JWT ou X-Cron-Secret)
```

### Algoritmo (`CronRunner.run(target_date)`)

```
1. Busca todas as recorrências onde is_due_on(recurrence, target_date) == True
2. Para cada recorrência:
   a. Verifica se já existe Invoice com (recurrence_id, scheduled_date=target_date, status='success')
      → se sim: pula (idempotência)
   b. Busca ou cria Invoice com status='pending' para (recurrence_id, scheduled_date=target_date)
      → se já existe com status='error': reutiliza e redefine para 'pending'
   c. Atualiza Invoice para status='processing'
   d. Chama DpsPoller.emit_and_poll(payload) → EmissionResult
   e. Atualiza Invoice com resultado (status, nf_number, pdf_url, xml_sent, xml_response,
      error_message, emission_date)
3. Envia e-mail de resumo (NotificationService.send_summary)
4. Retorna CronResult
```

### Tolerância a falhas individuais

Cada emissão roda em `try/except`. Uma falha em uma nota não interrompe as demais.
Exceções inesperadas são capturadas, registradas como `error` no Invoice e incluídas
no resumo do e-mail.

### Processamento sequencial

As emissões rodam **sequencialmente** (não em paralelo). Razão: o `nDPS` é
incremental e o polling de cada nota pode levar ~1 minuto. Volume esperado é de
dezenas de notas por mês — processamento paralelo não é necessário.

### Idempotência — botão manual

O botão manual chama o mesmo `POST /cron/run`. A regra do passo 2a garante que notas
já emitidas com sucesso no dia não são reprocessadas. Apenas as com `status='error'`
ou `status='pending'` (não tentadas ainda) são processadas.

---

## Regra do último dia do mês

Delegada inteiramente para `recurrences.domain.rules.is_due_on` e
`resolve_emission_date`. O `CronRunner` apenas chama `is_due_on(recurrence, today)`.

---

## Notificação por e-mail (`NotificationService`)

```
app/modules/cron/
  application/
    notification_service.py   # NotificationService
```

Enviada ao final de cada execução do job, independentemente de haver sucesso ou erro.

### Biblioteca

`aiosmtplib` — cliente SMTP assíncrono compatível com FastAPI/asyncio.

### Configurações

| Variável | Descrição |
|----------|-----------|
| `SMTP_HOST` | Servidor SMTP |
| `SMTP_PORT` | Porta (default `587`) |
| `SMTP_USER` | Usuário SMTP |
| `SMTP_PASSWORD` | Senha SMTP |
| `SMTP_USE_TLS` | `True` / `False` (default `True`) |
| `NOTIFICATION_EMAIL` | Destinatário do e-mail de resumo |
| `NOTIFICATION_FROM` | Remetente (default igual a `SMTP_USER`) |

### Conteúdo do e-mail

**Assunto:** `NFS-e — Resumo de emissão: {data} ({N} sucesso, {M} erro)`

**Corpo (HTML):**

```
Resumo da emissão do dia {data}

✅ {N} nota(s) emitida(s) com sucesso
❌ {M} nota(s) com falha

--- Sucessos ---
• Brand Open — NF nº 123456 [PDF]
• Empresa X  — NF nº 123457 [PDF]

--- Erros ---
• Empresa Y — Timeout ao aguardar processamento da Betha.

---
Emissão realizada automaticamente pelo sistema Brand Open NFS-e.
```

Se `SMTP_HOST` não estiver configurado: log de aviso, sem erro.

---

## Docker Compose — cron diário

Serviço adicional no `docker-compose.yml`:

```yaml
cron:
  image: alpine:3.19
  environment:
    - CRON_SECRET=${CRON_SECRET}
    - API_URL=http://api:8000
  command: >
    sh -c "echo '0 8 * * * wget -qO- --header=\"X-Cron-Secret: $$CRON_SECRET\"
    --post-data=\"\" $$API_URL/cron/run' | crontab - && crond -f -l 2"
  depends_on:
    - api
  restart: unless-stopped
```

Horário: **08h00 (horário do servidor)**. Configurável via `CRON_SCHEDULE`
(padrão `0 8 * * *`).

---

## Configurações adicionais (`settings.py`)

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `CRON_SECRET` | `str` | — | Segredo para autenticar o cron externo |
| `SMTP_HOST` | `str \| None` | `None` | Se `None`, e-mail desativado |
| `SMTP_PORT` | `int` | `587` | |
| `SMTP_USER` | `str \| None` | `None` | |
| `SMTP_PASSWORD` | `str \| None` | `None` | |
| `SMTP_USE_TLS` | `bool` | `True` | |
| `NOTIFICATION_EMAIL` | `str \| None` | `None` | Destinatário |
| `NOTIFICATION_FROM` | `str \| None` | `None` | Remetente |

---

## Autenticação dupla (`validate_cron_auth`)

```python
async def validate_cron_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer, auto_error=False),
) -> None:
    # Tenta Bearer JWT (sessão normal)
    if credentials:
        decode_access_token(credentials.credentials)  # lança se inválido
        return
    # Tenta X-Cron-Secret
    secret = request.headers.get("X-Cron-Secret")
    if secret and secret == settings.CRON_SECRET:
        return
    raise UnauthorizedError("Autenticação inválida para o endpoint de cron.")
```

---

## Testes

### Unitários (`tests/unit/modules/cron/`)

- `CronRunner.run`: recorrência sem Invoice → emite; Invoice com `status='success'`
  existente → pula; Invoice com `status='error'` → reprocessa.
- Falha em uma nota não interrompe as demais.
- `NotificationService`: template de e-mail com N sucessos e M erros.

### Integração (`tests/integration/modules/cron/`)

- Job completo com mock do `DpsPoller` (retorna `EmissionResult` pré-definido).
- Idempotência: rodar `POST /cron/run` duas vezes no mesmo dia não duplica emissões
  bem-sucedidas.
- Autenticação: JWT válido → 200; `X-Cron-Secret` válido → 200; sem auth → 401;
  secret errado → 401.

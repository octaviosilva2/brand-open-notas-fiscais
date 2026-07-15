---
name: auth-ui
description: Spec da tela de autenticação — login por e-mail e senha
metadata:
  type: project
---

# Spec — Autenticação (UI)

## Contexto

Tela de login única — usuária fixa (a responsável). O backend de auth (módulo `auth` +
módulo `users`) já existe e expõe `POST /auth/login`. Esta spec cobre apenas
o frontend.

---

## Rotas

| Rota | Componente | Comportamento |
|------|-----------|--------------|
| `/login` | `LoginPage` | Pública — redireciona para `/invoices` se já autenticado |
| Qualquer rota protegida sem JWT | — | Redireciona para `/login` |

---

## Tela de login

```
┌───────────────────────────────────────────┐
│                                           │
│          Brand Open — NFS-e               │
│                                           │
│   E-mail                                  │
│   [_________________________________]     │
│                                           │
│   Senha                                   │
│   [_________________________________] 👁  │
│                                           │
│   [          Entrar          ]            │
│                                           │
│   [mensagem de erro, se houver]           │
│                                           │
└───────────────────────────────────────────┘
```

Layout centralizado vertical e horizontalmente. Card com largura máxima de 400 px.

---

## Comportamento

**Campos:**
- E-mail: `type="email"`, autofocus ao montar.
- Senha: `type="password"` com botão de toggle de visibilidade (👁).
- Ambos obrigatórios — erro inline se submetido vazio.

**Submissão (`POST /auth/login`):**
- Botão "Entrar" desabilitado com spinner enquanto a requisição estiver em andamento.
- `Enter` no campo de senha submete o formulário.

**Sucesso:**
- Armazena o JWT em `localStorage` com chave `nfse_token`.
- Redireciona para `/invoices`.

**Erro 401:**
- Exibe mensagem abaixo do formulário: _"E-mail ou senha incorretos."_
- Limpa o campo de senha; foca no campo de e-mail.

**Erro 5xx / rede:**
- Exibe: _"Erro ao conectar ao servidor. Tente novamente."_

---

## Guarda de rotas (`AuthGuard`)

Componente wrapper que protege todas as rotas exceto `/login`:

```
verificar localStorage["nfse_token"]
  → presente: renderiza rota normalmente
  → ausente: redireciona para /login
```

Respostas `401` de qualquer endpoint da API (interceptadas no cliente HTTP global)
limpam o token e redirecionam para `/login`.

---

## Navegação principal

Após login, o app exibe barra lateral (ou barra superior em mobile) com as rotas:

| Item | Rota |
|------|------|
| Notas Fiscais | `/invoices` (default após login) |
| Próximas Notas | `/upcoming` |
| Recorrências | `/recurrences` |
| Clientes | `/clients` |

Botão de logout: limpa `localStorage["nfse_token"]` e redireciona para `/login`.

---

## Componentes

| Componente | Uso |
|-----------|-----|
| `LoginPage` | Tela de login |
| `AuthGuard` | HOC de proteção de rotas |
| `useAuth` | Hook: estado de autenticação, `login()`, `logout()` |
| `apiClient` | Instância `axios`/`fetch` com interceptor de `401` global |

---

## Armazenamento do token

Token JWT em `localStorage["nfse_token"]`.

Enviado em todas as requisições autenticadas como:
```
Authorization: Bearer {token}
```

Sem renovação automática — ao expirar, o interceptor de `401` redireciona para login.
Configurar expiração longa o suficiente para o uso diário (ex: 24 h ou 7 dias —
conforme `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` no backend).

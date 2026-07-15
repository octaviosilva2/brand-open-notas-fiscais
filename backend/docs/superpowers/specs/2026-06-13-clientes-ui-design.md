---
name: clientes-ui
description: Spec do módulo de clientes (tomadores) — Frontend React (TypeScript)
metadata:
  type: project
---

# Spec — Módulo Clientes (UI)

## Contexto

Interface de cadastro e gerenciamento de tomadores de serviço. Consome a API descrita
em `2026-06-13-clientes-api-design.md`. O frontend a ser construído substituirá o
protótipo atual (wizard de emissão manual), adotando o mesmo estilo visual minimalista
já estabelecido.

---

## Rotas

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/clients` | `ClientsListPage` | Listagem de clientes |
| `/clients/new` | `ClientFormPage` | Cadastro de novo cliente |
| `/clients/:id/edit` | `ClientFormPage` | Edição de cliente existente |

---

## Tela 1 — Listagem (`/clients`)

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Clientes                              [+ Novo cliente]      │
├─────────────────────────────────────────────────────────────┤
│  🔍 Buscar por nome ou CPF/CNPJ...                          │
├──────────────────┬──────────────┬──────────┬────────────────┤
│ Nome             │ CPF/CNPJ     │ E-mail   │ Ações          │
├──────────────────┼──────────────┼──────────┼────────────────┤
│ Brand Open       │ 11.222.333/… │ …        │ Editar Excluir │
│ …                │ …            │ …        │ …              │
├─────────────────────────────────────────────────────────────┤
│ ← 1 2 3 →                              20 itens por página  │
└─────────────────────────────────────────────────────────────┘
```

### Comportamento

- **Busca**: debounce de 300 ms; atualiza a query `?search=` na URL (preserva ao
  navegar para edição e voltar).
- **Paginação**: query params `?page=` na URL.
- **CPF/CNPJ** exibido formatado: CPF → `000.000.000-00`; CNPJ → `00.000.000/0000-00`.
- **Excluir**: abre `<ConfirmDialog>` com texto _"Tem certeza que deseja excluir
  [Nome]?"_. Se a API retornar 409, fecha o dialog e exibe banner de erro: _"Cliente
  possui recorrências vinculadas e não pode ser excluído."_
- **Estado vazio** (sem busca): _"Nenhum cliente cadastrado. Clique em 'Novo cliente'
  para começar."_
- **Estado vazio** (com busca): _"Nenhum cliente encontrado para '[termo]'."_
- **Estado de carregamento**: skeleton de tabela (linhas em placeholder).

---

## Tela 2 — Formulário (`/clients/new` e `/clients/:id/edit`)

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ← Clientes / Novo cliente                                   │
├─────────────────────────────────────────────────────────────┤
│  CPF / CNPJ *          [__.___.___/____-__]                 │
│  Nome / Razão Social * [_________________________________]   │
│  Inscrição Municipal   [_____________________________]       │
│  Telefone              [_____________________________]       │
│  E-mail                [_____________________________]       │
│                                                             │
│  [ ] Informar endereço                                      │
│  ┌─ (visível só se marcado) ────────────────────────────┐   │
│  │  CEP *              [________]                        │   │
│  │  Logradouro *       [__________________________]      │   │
│  │  Número *           [__________]                      │   │
│  │  Complemento        [__________________________]      │   │
│  │  Bairro *           [__________________________]      │   │
│  │  Município (IBGE) * [_______]                         │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                             │
│                              [Cancelar]  [Salvar]           │
└─────────────────────────────────────────────────────────────┘
```

### Comportamento dos campos

**CPF/CNPJ**
- Aceita somente dígitos; aplica máscara ao digitar:
  - 1–11 dígitos → máscara CPF: `000.000.000-00`
  - 12–14 dígitos → muda para máscara CNPJ: `00.000.000/0000-00`
- Validação: 11 ou 14 dígitos ao sair do campo.

**CEP — autopreenchimento via ViaCEP**
- Ao sair do campo CEP (blur) com 8 dígitos, chama
  `https://viacep.com.br/ws/{cep}/json/`.
- Preenche automaticamente: Logradouro (`logradouro`), Bairro (`bairro`), Município
  IBGE (`ibge`).
- Campos preenchidos via ViaCEP ficam editáveis (o usuário pode corrigir).
- Se o CEP não for encontrado: exibe mensagem abaixo do campo _"CEP não encontrado."_;
  campos de endereço permanecem vazios e editáveis.
- Se a requisição falhar (rede): ignora silenciosamente, campos ficam editáveis.

**Toggle "Informar endereço"**
- Desmarcá-lo após preencher endereço: limpa todos os campos de endereço do estado
  (não apenas os oculta).

**Município (código IBGE)**
- Campo de texto simples; 7 dígitos numéricos.
- Preenchido automaticamente pelo ViaCEP quando disponível.
- Editável manualmente caso o ViaCEP não retorne ou o usuário prefira corrigir.

### Validação

Todos os erros aparecem abaixo do campo respectivo.

| Campo | Regra |
|-------|-------|
| CPF/CNPJ | Obrigatório; 11 ou 14 dígitos |
| Nome | Obrigatório; não vazio |
| E-mail | Formato válido quando preenchido |
| CEP | 8 dígitos quando endereço ativo |
| Logradouro, Número, Bairro, Município IBGE | Obrigatórios quando endereço ativo |
| Município IBGE | Exatamente 7 dígitos quando preenchido |

Erro de CPF/CNPJ duplicado (409 da API): exibido no campo CPF/CNPJ como _"Este
documento já está cadastrado."_

### Modo edição

- Ao entrar em `/clients/:id/edit`, busca `GET /clients/:id` e preenche o formulário.
- O toggle "Informar endereço" começa marcado se o cliente já tiver endereço salvo.
- Submissão usa `PATCH /clients/:id` com apenas os campos alterados.

### Submissão

- Botão **Salvar** desabilitado enquanto a requisição estiver em andamento (spinner).
- Sucesso: redireciona para `/clients` com toast _"Cliente salvo com sucesso."_
- **Cancelar**: navega de volta para `/clients` sem confirmar (sem dirty-check).

---

## Componentes

| Componente | Uso |
|-----------|-----|
| `ClientsListPage` | Página de listagem |
| `ClientFormPage` | Página de formulário (create + edit) |
| `ConfirmDialog` | Modal de confirmação de exclusão (reutilizável) |
| `useClients` | Hook: listagem paginada com busca (`GET /clients`) |
| `useClient` | Hook: busca por ID (`GET /clients/:id`) |
| `useSaveClient` | Hook: create (`POST`) ou update (`PATCH`) |
| `useDeleteClient` | Hook: exclusão (`DELETE`) |
| `useViaCep` | Hook: autopreenchimento de endereço |

---

## Estado e navegação

- Busca e página persistidas como query params na URL (`?search=&page=`).
- Formulário usa estado local (`useState` / `useReducer`) — sem store global.
- Toast de sucesso gerenciado por contexto global de notificações (a definir na
  estrutura base do app).

---

## Integração com a API

Base URL configurável via variável de ambiente `VITE_API_URL`.

Todos os endpoints exigem header `Authorization: Bearer <token>` (JWT obtido no
login — módulo Auth).

Erros HTTP mapeados:
| Status | Tratamento |
|--------|-----------|
| 401 | Redireciona para `/login` |
| 404 | Exibe _"Cliente não encontrado."_ e redireciona para listagem |
| 409 | Exibe mensagem de conflito no campo ou banner |
| 5xx | Banner de erro genérico: _"Erro interno. Tente novamente."_ |

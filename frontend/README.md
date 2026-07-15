# Frontend — Emissão de NFS-e (réplica do wizard e-Nota / Betha)

Réplica fiel do formulário **"Adicionando DPS"** do e-Nota Cloud (Betha / Jaraguá
do Sul), para preenchimento dos campos da DPS (Declaração de Prestação de Serviço).

> **Sem backend.** Nada é salvo nem emitido. Ao clicar em **Emitir DPS**, o app
> apenas monta e exibe o payload `infDPS` que *seria* enviado à API oficial — é o
> ponto de integração futura. Os campos vêm vazios (como na tela original).

## Rodar

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # typecheck + build de produção
npm run lint
```

## Estrutura

```
src/
  types/dps.ts            Modelo de dados espelhando a árvore infDPS (ver ../campos.md)
  state/DpsContext.tsx    Estado global (Context + reducer; update via clone+mutação)
  validation/dpsSchema.ts Validação por etapa (obrigatórios/choice) na hora do AVANÇAR
  calc/derived.ts         Valores calculados (base, ISSQN, retenções, líquido) — só exibição
  payload/buildInfDps.ts  Monta o objeto infDPS a partir do formulário (omite calculados)
  api/dpsClient.ts        STUB submitDps() — troque por fetch quando a API existir
  api/lookups.ts          STUBS de busca (município/país/lista/NBS) com mock data
  components/             Primitivos de form + PersonFields/AddressFields/Stepper
  pages/                  PessoasStep · ServicoStep · ValoresStep · RevisarStep
```

## Wizard

1. **Pessoas** — data da prestação, Tomador e Intermediário (Não informado / Brasil / Exterior).
2. **Serviço** — local da prestação, natureza, retenção, lista de serviço, NBS, descrição,
   detalhes adicionais condicionais (obra / imóvel / evento), informações complementares.
3. **Valores** — valor/descontos, dedução/redução (percentual / valor / documento),
   alíquota (tabela do Simples), tributação federal (PIS/COFINS + retenções).
4. **Revisar** — consolidação somente-leitura + botão **Emitir DPS** (mostra o payload).

## Integração futura com o backend

Tudo o que toca a "rede" está isolado em `src/api/`:

- **`dpsClient.submitDps(dps)`** já retorna `Promise<DpsResult>`. Basta trocar o corpo
  por um `fetch('/api/dps', { method: 'POST', body: JSON.stringify(buildInfDps(dps)) })`.
- **`lookups.ts`** expõe `searchMunicipios/Paises/ListaServico/NBS` retornando
  `Promise<Option[]>`. Trocar os arrays mock por chamadas de API não afeta a UI.
- **`buildInfDps`** mapeia o estado do formulário 1:1 para a estrutura `infDPS` do XML
  (ver `../campos.md`). Campos calculados pelo sistema **não** entram no payload.

## Referência de campos

`../campos.md` é a fonte da verdade (campo de tela ↔ tag XML, obrigatoriedades,
tamanhos, choices). `../campos_preenchidos.md` descreve o caso de uso do brand_open.

# Mapeamento de campos — NFS-e Betha (Jaraguá do Sul)

> Origem: leiaute oficial da DPS (Declaração de Prestação de Serviço — padrão nacional NFS-e), arquivo `layout-dps-0b89fdfe3968c73161bd2121495f921e.xlsx`.
> Cruzamento: formulário web do **e-Nota Cloud (Betha)** × tags XML do leiaute nacional.

**Legenda**
- **Obrig.**: `O` = obrigatório · `Op` = opcional · `CE` = *choice* (informa um OU outro do grupo, mutuamente exclusivos)
- **Tag XML**: nome do elemento. **Caminho XML**: caminho completo a partir de `infDPS`.
- Endereço **nacional** usa o grupo `end/endNac` (cMun, CEP) · endereço **exterior** usa `end/endExt` (cPais, cEndPost, xCidade, xEstProvReg).
- ⚠️ **Tela × XML**: alguns campos são *digitados em uma página da tela* diferente de onde sua *tag mora no XML*. Esses casos estão marcados com o aviso "Tela × XML" na seção correspondente.

---

## Tomador do serviço

Opção na tela: **Tomador não informado** · **Brasil** · **Exterior**.

### Brasil

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| CPF/CNPJ | O (CE) | `infDPS/toma` | `CPF` / `CNPJ` | 11 / 14 |
| Nome/Razão Social | O | `infDPS/toma` | `xNome` | 150 |
| Inscrição Municipal | Op | `infDPS/toma` | `IM` | 15 |
| CAEPF (pessoa física) | Op | `infDPS/toma` | `CAEPF` | 14 |
| Telefone | Op | `infDPS/toma` | `fone` | 6–20 |
| Email | Op | `infDPS/toma` | `email` | 1–80 |
| Informar endereço (grupo) | Op | `infDPS/toma/end` | `end` | — |
| › CEP | O* | `infDPS/toma/end/endNac` | `CEP` | 8 |
| › Logradouro | O* | `infDPS/toma/end` | `xLgr` | 1–255 |
| › Número | O* | `infDPS/toma/end` | `nro` | 1–60 |
| › Complemento | Op | `infDPS/toma/end` | `xCpl` | 1–156 |
| › Bairro | O* | `infDPS/toma/end` | `xBairro` | 1–60 |
| › Município (cód. IBGE) | O* | `infDPS/toma/end/endNac` | `cMun` | 7 |

\* Obrigatório apenas se "Informar endereço" for marcado (grupo `end` é opcional). Ordem dos campos acima = ordem na tela e-Nota.

### Exterior

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| NIF (nº fiscal no exterior) | O (CE) | `infDPS/toma` | `NIF` | 40 |
| Motivo não informar NIF (0/1/2) | O (CE) | `infDPS/toma` | `cNaoNIF` | 1 |
| Nome/Razão Social | O | `infDPS/toma` | `xNome` | 150 |
| Telefone | Op | `infDPS/toma` | `fone` | 6–20 |
| Email | Op | `infDPS/toma` | `email` | 1–80 |
| Informar endereço (grupo) | Op | `infDPS/toma/end` | `end` | — |
| › País (cód. ISO) | O* | `infDPS/toma/end/endExt` | `cPais` | 2 |
| › Código postal | O* | `infDPS/toma/end/endExt` | `cEndPost` | — |
| › Cidade | O* | `infDPS/toma/end/endExt` | `xCidade` | 1–60 |
| › Estado/Província/Região | O* | `infDPS/toma/end/endExt` | `xEstProvReg` | 1–60 |
| › Logradouro | O* | `infDPS/toma/end` | `xLgr` | 1–255 |
| › Número | O* | `infDPS/toma/end` | `nro` | 1–60 |
| › Complemento | Op | `infDPS/toma/end` | `xCpl` | 1–156 |
| › Bairro | O* | `infDPS/toma/end` | `xBairro` | 1–60 |

> `cNaoNIF`: 0 = não informado · 1 = dispensado do NIF · 2 = não exigência do NIF.

---

## Intermediário do serviço

Opção na tela: **Intermediário não informado** · **Brasil** · **Exterior**. Grupo `interm` inteiro é opcional (`0-1`); "não informado" = grupo omitido.

### Brasil

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| CPF/CNPJ | O (CE) | `infDPS/interm` | `CPF` / `CNPJ` | 11 / 14 |
| Nome/Razão Social | O | `infDPS/interm` | `xNome` | 150 |
| Inscrição Municipal | Op | `infDPS/interm` | `IM` | 15 |
| CAEPF (pessoa física) | Op | `infDPS/interm` | `CAEPF` | 14 |
| Telefone | Op | `infDPS/interm` | `fone` | 6–20 |
| Email | Op | `infDPS/interm` | `email` | 1–80 |
| Informar endereço (grupo) | Op | `infDPS/interm/end` | `end` | — |
| › CEP | O* | `infDPS/interm/end/endNac` | `CEP` | 8 |
| › Município (cód. IBGE) | O* | `infDPS/interm/end/endNac` | `cMun` | 7 |
| › Logradouro | O* | `infDPS/interm/end` | `xLgr` | 1–255 |
| › Número | O* | `infDPS/interm/end` | `nro` | 1–60 |
| › Complemento | Op | `infDPS/interm/end` | `xCpl` | 1–156 |
| › Bairro | O* | `infDPS/interm/end` | `xBairro` | 1–60 |

\* Obrigatório apenas se "Informar endereço" for marcado.

### Exterior

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| NIF (nº fiscal no exterior) | O (CE) | `infDPS/interm` | `NIF` | 40 |
| Motivo não informar NIF (0/1/2) | O (CE) | `infDPS/interm` | `cNaoNIF` | 1 |
| Nome/Razão Social | O | `infDPS/interm` | `xNome` | 150 |
| Telefone | Op | `infDPS/interm` | `fone` | 6–20 |
| Email | Op | `infDPS/interm` | `email` | 1–80 |
| Informar endereço (grupo) | Op | `infDPS/interm/end` | `end` | — |
| › País (cód. ISO) | O* | `infDPS/interm/end/endExt` | `cPais` | 2 |
| › Código postal | O* | `infDPS/interm/end/endExt` | `cEndPost` | — |
| › Cidade | O* | `infDPS/interm/end/endExt` | `xCidade` | 1–60 |
| › Estado/Província/Região | O* | `infDPS/interm/end/endExt` | `xEstProvReg` | 1–60 |
| › Logradouro | O* | `infDPS/interm/end` | `xLgr` | 1–255 |
| › Número | O* | `infDPS/interm/end` | `nro` | 1–60 |
| › Complemento | Op | `infDPS/interm/end` | `xCpl` | 1–156 |
| › Bairro | O* | `infDPS/interm/end` | `xBairro` | 1–60 |

---

## Serviço (página "Serviço")

Grupo `infDPS/serv` (obrigatório, `1-1`).

### Dados do serviço

Ordem na tela e-Nota: País da prestação · Município da prestação · Natureza da operação · Tipo de retenção ISSQN · Lista de Serviço · NBS · Município de incidência ISSQN (somente leitura) · Descrição.

> ⚠️ **Tela × XML**: "Natureza da operação" e "Tipo de retenção ISSQN" são **digitados na página Serviço**, mas no XML pertencem ao grupo `valores/trib/tribMun` (detalhados em "Cálculo do ISSQN", abaixo).

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| País da prestação (cód. ISO) | O (CE) | `infDPS/serv/locPrest` | `cPaisPrestacao` | 2 |
| Local da prestação (município, cód. IBGE) | O (CE) | `infDPS/serv/locPrest` | `cLocPrestacao` | 7 |
| Natureza da operação (1 tributável / 2 imunidade / 3 exportação / 4 não incidência) | O | `infDPS/valores/trib/tribMun` | `tribISSQN` | 1 |
| Tipo de retenção ISSQN (1 não retido / 2 retido tomador / 3 retido interm.) | O | `infDPS/valores/trib/tribMun` | `tpRetISSQN` | 1 |
| Lista de Serviço *(ex: 17.01.01)* | O | `infDPS/serv/cServ` | `cTribNac` | 6 |
| Tributação municipal | Op | `infDPS/serv/cServ` | `cTribMun` | 3 |
| NBS *(ex: 114011400)* | O | `infDPS/serv/cServ` | `cNBS` | 9 |
| Município de incidência ISSQN | leitura | *derivado* | — (calculado) | — |

> `cLocPrestacao` × `cPaisPrestacao` são *choice*: município nacional **ou** país. `0000000` = Águas Marítimas.
> "Município de incidência ISSQN" aparece na tela **somente leitura** (preenchido pelo sistema a partir do local de prestação + item de serviço); não é digitado nem é tag própria da DPS.

### Detalhes adicionais do serviço

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Código interno do contribuinte | Op | `infDPS/serv/cServ` | `cIntContrib` | 20 |
| Documento de responsabilidade técnica (ART/RRT/DRT…) | Op | `infDPS/serv/infoCompl` | `idDocTec` | 1–40 |
| Documento de referência (chave/nº nota base) | Op¹ | `infDPS/serv/infoCompl` | `docRef` | 1–255 |
| Nº pedido / ordem de compra / OS | Op | `infDPS/serv/infoCompl` | `xPed` | 1–60 |
| Item do pedido | Op | `infDPS/serv/infoCompl/gItemPed` | `xItemPed` | 1–60 |

¹ `docRef` é **obrigatório** quando a nota é emitida pelo Tomador ou Intermediário.

### Descrição e informações complementares

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Descrição do serviço | O | `infDPS/serv/cServ` | `xDescServ` | 1000 |
| Informações complementares (campo livre) | Op | `infDPS/serv/infoCompl` | `xInfComp` | 2000 |

> **Grupos condicionais** que só aparecem para certos itens da lista de serviço (não se aplicam a 17.01.01 — consultoria):
> - `serv/obra` — obras de construção civil (CNO/CIB, endereço da obra)
> - `serv/atvEvento` — atividades de evento (nome, datas, endereço)
> - `serv/lsadppu` — locação/arrendamento de rodovia, postes, cabos, dutos
> - `serv/comExt` — operações com exterior (modo de prestação, moeda, mecanismos de fomento)

---

## Valores (página "Valores")

Grupo `infDPS/valores` (obrigatório, `1-1`).

### Valores

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Valor do serviço (R$) | O | `infDPS/valores/vServPrest` | `vServ` | 1–15V2 |
| Valor recebido (R$) | Op | `infDPS/valores/vServPrest` | `vReceb` | 1–15V2 |
| Desconto incondicionado (R$) | Op | `infDPS/valores/vDescCondIncond` | `vDescIncond` | 1–15V2 |
| Desconto condicionado (R$) | Op | `infDPS/valores/vDescCondIncond` | `vDescCond` | 1–15V2 |

### Dedução/Redução à base de cálculo do ISSQN

Grupo `infDPS/valores/vDedRed` (opcional, `0-1`). Três modalidades — escolha uma: **Valor**, **Percentual** ou **Documento**.

> ⚠️ **Tela × XML**: na tela e-Nota, este bloco ("Dedução/Redução à base de cálculo do ISSQN", página **Valores**) mostra também o campo **"Regime especial de tributação"** (`regEspTrib`), que no XML pertence a `prest/regTrib` (ver seção "Prestador"). O seletor "Tipo de dedução/redução" controla a modalidade abaixo.

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Percentual de dedução/redução (%) | O (CE) | `infDPS/valores/vDedRed` | `pDR` | 1–3V2 |
| Valor de dedução/redução (R$) | O (CE) | `infDPS/valores/vDedRed` | `vDR` | 1–15V2 |

**Modalidade "Documento"** — grupo `vDedRed/documentos/docDedRed` (repete `1–1000`):

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Tipo da dedução/redução (01–08, 99) | O | `…/vDedRed/documentos/docDedRed` | `tpDedRed` | 2 |
| Descrição (quando tipo = 99) | Op | `…/docDedRed` | `xDescOutDed` | 150 |
| Data emissão do documento | O | `…/docDedRed` | `dtEmiDoc` | — |
| Valor total dedutível no documento (R$) | O | `…/docDedRed` | `vDedutivelRedutivel` | 1–15V2 |
| Valor usado para deduzir nesta NFS-e (R$) | O | `…/docDedRed` | `vDeducaoReducao` | 1–15V2 |
| Chave NFS-e | O (CE) | `…/docDedRed` | `chNFSe` | 50 |
| Chave NF-e | O (CE) | `…/docDedRed` | `chNFe` | 44 |
| Outra NFS-e municipal (cód.mun/nº/cód.verif.) | O (CE) | `…/docDedRed/NFSeMun` | `cMunNFSeMun` / `nNFSeMun` / `cVerifNFSeMun` | 7 / 15 / 9 |
| NF/NFS não eletrônica (nº/modelo/série) | O (CE) | `…/docDedRed/NFNFS` | `nNFS` / `modNFS` / `serieNFS` | 7 / 15 / 9 |
| Outro documento fiscal | O (CE) | `…/docDedRed` | `nDocFisc` | 255 |
| Outro documento não fiscal | O (CE) | `…/docDedRed` | `nDoc` | 255 |
| Dados do fornecedor (CPF/CNPJ/NIF, nome, endereço…) | Op | `…/docDedRed/fornec` | `fornec` | — |

> Identificação do documento é *choice*: NFS-e, NF-e, outra NFS-e municipal, NF/NFS não eletrônica, outro doc. fiscal **ou** outro doc. não fiscal.

### Cálculo do ISSQN

Grupo `infDPS/valores/trib/tribMun` (`1-1`). **As duas telas (com/sem dedução) enviam os mesmos campos** — a diferença é só a base de cálculo exibida (com dedução: base = valor do serviço − deduções/reduções). Base de cálculo e valor do ISSQN são **calculados pelo sistema**, não são tags da DPS.

> ⚠️ **Tela × XML**: na tela e-Nota, `tribISSQN` (Natureza da operação) e `tpRetISSQN` (Tipo de retenção) são preenchidos na página **Serviço** (ver acima). Na página **Valores** aparecem apenas a **Alíquota** e os valores calculados (base de cálculo, valor ISSQN, valor líquido).

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Tributação do ISSQN *(tela: página Serviço)* | O | `…/trib/tribMun` | `tribISSQN` | 1 |
| Alíquota do ISSQN (%) | Op¹ | `…/trib/tribMun` | `pAliq` | 1V2 |
| Tipo de retenção *(tela: página Serviço)* | O | `…/trib/tribMun` | `tpRetISSQN` | 1 |
| País do resultado (exportação) | Op² | `…/trib/tribMun` | `cPaisResult` | 2 |
| Tipo de imunidade (0–5) | Op³ | `…/trib/tribMun` | `tpImunidade` | 1 |
| Benefício municipal (nº/redução R$/redução %) | Op | `…/trib/tribMun/BM` | `nBM` / `vRedBCBM` / `pRedBCBM` | 14 / 15V2 / 3V2 |
| Suspensão de exigibilidade (tipo + nº processo) | Op | `…/trib/tribMun/exigSusp` | `tpSusp` / `nProcesso` | 1 / 30 |

¹ Fornecida pelo sistema se o município pertence ao Sistema Nacional; informada pelo emitente caso contrário. Para emitente **optante do Simples Nacional**, a tela mostra um seletor "Utilizar alíquota do faturamento" + uma **tabela de Anexos/faixas** (ex.: Anexo III · 1ª faixa = `2,01%`); **seleciona-se a linha**, não se digita o valor.
² Obrigatório se `tribISSQN` = 3 (exportação).
³ Somente se `tribISSQN` = 2 (imunidade).

### Tributação Federal

Grupo `infDPS/valores/trib/tribFed` (opcional, `0-1`).

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| **PIS/COFINS — CST** (00–09) | O* | `…/trib/tribFed/piscofins` | `CST` | 2 |
| Base de cálculo PIS/COFINS (R$) | Op | `…/piscofins` | `vBCPisCofins` | 1–15V2 |
| Alíquota PIS (%) | Op | `…/piscofins` | `pAliqPis` | 1–2V2 |
| Alíquota COFINS (%) | Op | `…/piscofins` | `pAliqCofins` | 1–2V2 |
| Valor PIS (R$) | Op | `…/piscofins` | `vPis` | 1–15V2 |
| Valor COFINS (R$) | Op | `…/piscofins` | `vCofins` | 1–15V2 |
| Tipo retenção PIS/COFINS (1–4) | Op | `…/piscofins` | `tpRetPisCofins` | 1 |
| Retenção CP (INSS) (R$) | Op | `…/trib/tribFed` | `vRetCP` | 1–15V2 |
| Retenção IRRF (R$) | Op | `…/trib/tribFed` | `vRetIRRF` | 1–15V2 |
| Retenção CSLL (R$) | Op | `…/trib/tribFed` | `vRetCSLL` | 1–15V2 |

\* No XML, o grupo `piscofins` é opcional e o `CST` só é obrigatório se o grupo for informado. **Na tela e-Nota**, porém, o campo **"Situação Tributária PIS/COFINS" é obrigatório** (seleção). Opções do dropdown:
> - **Nenhum** → sem PIS/COFINS (grupo `piscofins` **não enviado**) — é a 1ª opção e satisfaz o campo obrigatório.
> - Operação Tributável com Alíquota Básica · Diferenciada · por Unidade de Medida de Produto → cada uma corresponde a um `CST` e habilita os demais campos (base, alíquotas, valores).

> **Totais aproximados de tributos** (Lei 12.741/2012) — grupo `valores/trib/totTrib` (`1-1`): `vTotTribFed`/`vTotTribEst`/`vTotTribMun` (valores) ou `pTotTribFed`/`pTotTribEst`/`pTotTribMun` (percentuais), ou `indTotTrib=0` para não informar. Para Simples Nacional: `pTotTribSN`.

---

## Dados da prestação (cabeçalho da DPS)

Etapa inicial — `infDPS` raiz. Vários campos são **gerados pelo sistema** (não digitados).

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Data da prestação do serviço | O | `infDPS` | `dCompet` | AAAA-MM-DD |
| Competência (mês/ano) | O | `infDPS` | *(derivado de `dCompet`)* | — |
| Emitente da DPS (1 prestador / 2 tomador / 3 interm.) | O | `infDPS` | `tpEmit` | 1 |
| Data/hora de emissão | sistema | `infDPS` | `dhEmi` | UTC |
| Série / Número da DPS | sistema | `infDPS` | `serie` / `nDPS` | 5 / 15 |
| Localidade emissora (cód. IBGE) | sistema | `infDPS` | `cLocEmi` | 7 |

> Se a nota for emitida por tomador/intermediário, abrem-se `cMotivoEmisTI` e `chNFSeRej`. Substituição de NFS-e usa o grupo `subst` (`chSubstda`, `cMotivo`, `xMotivo`).

---

## Prestador (emitente)

Grupo `infDPS/prest` (`1-1`). Normalmente **pré-preenchido** com os dados da clínica/empresa emitente. Identificação e endereço seguem o mesmo padrão do Tomador (`CPF`/`CNPJ`/`NIF`, `IM`, `xNome`, `end/endNac`…). Campo que aparece na Revisão:

### Regime de tributação — grupo `prest/regTrib` (`1-1`)

| Campo (tela) | Obrig. | Caminho XML | Tag XML | Tam. |
|---|---|---|---|---|
| Situação Simples Nacional (1 não optante / 2 MEI / 3 ME-EPP) | O | `infDPS/prest/regTrib` | `opSimpNac` | 1 |
| Regime de apuração SN (1/2/3) | Op¹ | `infDPS/prest/regTrib` | `regApTribSN` | 1 |
| **Regime especial de tributação** (0 Nenhum / 1 Ato Cooperado / 2 Estimativa / 3 Microempresa Municipal / …) | O | `infDPS/prest/regTrib` | `regEspTrib` | 1 |

¹ Só para optante ME/EPP (`opSimpNac = 3`).

> ⚠️ **Tela × XML**: `regEspTrib` ("Regime especial de tributação") **não tem tela própria de Prestador** no fluxo e-Nota — é exibido na página **Valores**, no bloco "Dedução/Redução" (ver acima). `opSimpNac`/`regApTribSN` vêm do **cadastro do emitente** (o cabeçalho mostra "Optante do Simples") e alimentam a tabela de alíquotas do Cálculo do ISSQN.
> Na Revisão, o bloco **"Regime Especial e Retenção"** combina: `regEspTrib` (= "Regime especial de tributação: Nenhum") + `tribMun/tpRetISSQN` (= "Tipo retenção: Não Retido").

---

## Revisão (página final — etapa "Revisar")

Tela **somente leitura** que consolida as 3 etapas (Pessoas → Serviço → Valores) antes de **Emitir DPS**. Não há campos de entrada novos; abaixo o de-para do que é exibido:

| Rótulo na revisão | Origem (já mapeado) |
|---|---|
| Data da prestação / Competência | `dCompet` |
| Natureza da operação | `tribMun/tribISSQN` (ex: "Operação tributável" = 1) |
| **CTN** *(ex: 170101)* | `serv/cServ/cTribNac` — mesmo campo de "Lista de Serviço" (sem os pontos) |
| País | `serv/locPrest/cPaisPrestacao` |
| Município da prestação | `serv/locPrest/cLocPrestacao` |
| **Município de incidência** | *derivado* — município sujeito ativo do ISSQN (onde o imposto é devido); não é tag própria da DPS, é calculado a partir do local de prestação + item de serviço |
| Regime especial de tributação | `prest/regTrib/regEspTrib` |
| Tipo retenção | `tribMun/tpRetISSQN` |
| Valor total do serviço | `valores/vServPrest/vServ` |
| Desconto incondicionado / condicionado | `vDescIncond` / `vDescCond` |
| Total deduções/reduções | `valores/vDedRed` (soma) |
| Base de cálculo ISSQN | *calculado* (vServ − deduções/descontos) |
| Alíquota ISSQN | `tribMun/pAliq` |
| Valor ISSQN | *calculado* (base × alíquota) |
| Valor PIS / COFINS | `tribFed/piscofins/vPis` / `vCofins` |
| Total retenções | *calculado* (soma das retenções) |
| Valor Líquido | *calculado* (vServ − retenções) |

> **Atenção automação**: os campos *calculados* (base de cálculo, valor ISSQN, total retenções, valor líquido) **não entram no XML da DPS** — o sistema/ADN os calcula. A automação envia apenas os campos de entrada mapeados nas seções acima.

---

<!-- Próxima seção opcional: IBS/CBS (reforma tributária) — entra se/quando necessário. -->

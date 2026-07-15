# Detalhamento — Automação de Emissão de NFS-e

## Contexto
Automação do processo de emissão mensal de Notas Fiscais de Serviço Eletrônicas (NFS-e), atualmente realizado manualmente pela responsável com duração aproximada de 2 horas por mês. A automação visa eliminar esse trabalho manual via integração com a API da Betha Sistemas (Web Service SOAP), com gerenciamento das configurações por meio de uma interface web.


## Escopo

### Dentro do escopo

- Interface web para cadastro e gerenciamento das configurações de emissão
Cadastro de clientes pela própria interface
- Agendamento recorrente de emissão de NFS-e por cliente (dia do mês + data de término opcional)
- Inativação de recorrências
- Visualização de notas fiscais geradas (histórico)
- Visualização de notas fiscais agendadas (próximas emissões)
- Emissão de NFS-e via API da Betha Sistemas
- Consulta de status de processamento (polling assíncrono)
- Registro de logs de envio e retorno da API
- Notificação por e-mail ao final de cada execução com resumo das notas emitidas (links dos PDFs) e erros ocorridos
- Botão na interface para acionar o cron manualmente

### Fora do escopo

- Cancelamento de notas via API — será feito manualmente pela responsável diretamente no sistema da prefeitura
- Retentativas automáticas em caso de falha — a responsável aciona manualmente pela interface

## Interface Web

### Usuários

- Usuário único: a responsável
- Criação de conta feita diretamente no banco de dados pelo administrador
- Login por e-mail e senha

### Telas

#### Clientes

- Listagem de clientes cadastrados
- Cadastro e edição de cliente
Campos: a definir com a responsável (ver Itens 
- Pendentes)

#### Configurações de Emissão (Recorrências)

- Listagem de todas as recorrências (ativas e inativas)
- Cadastro de nova recorrência: cliente, valor, dia do mês, data de término (opcional), ativo/inativo
- Campos de nota por cliente (código do serviço, descrição, alíquota, competência): a definir com a responsável (ver - Itens Pendentes)
- Campo para inativar/reativar uma recorrência
- Recorrências com data de término atingida ficam inativas (não são excluídas)

#### Notas Fiscais Geradas

- Listagem das notas já processadas
Informações visíveis: cliente, data/hora de geração, status (sucesso ou erro), número da NF
- Ações disponíveis: baixar PDF, baixar XML, tentar emitir novamente (em caso de falha)
- Botão para acionar o cron manualmente (processa todos os agendamentos do dia que ainda não foram processados com sucesso)

#### Próximas Notas Fiscais

- Listagem de todas as emissões agendadas para um período selecionável
- Apenas visualização — sem edição por agendamento individual

#### Comportamento do agendamento

- Cada recorrência define: cliente, dia do mês, data de início, data de término (opcional)
- O cron roda uma vez por dia e emite as notas cujo dia agendado coincide com a data atual
- Se o dia agendado não existe no mês (ex: dia 31 em fevereiro), emite no último dia do mês
- Notas já processadas com sucesso no dia não são reprocessadas pelo botão manual
- O botão manual reprocessa apenas as que falharam ou ainda não foram processadas no dia

#### Design

- Estilo minimalista e funcional
- Foco em desktop, com suporte a uso mobile

## API — Betha Sistemas

### Autenticação

Exige certificado digital ICP-Brasil (e-CPF ou e-CNPJ), tipo A1 ou A3, em dois momentos:

- Assinatura do XML: o certificado deve conter o CNPJ do prestador ou da matriz
- Transmissão (mTLS): pode ser um CNPJ diferente do prestador, com permissão de "Autenticação Cliente".

## Logs

Registrar para cada nota processada:
- Data/hora do envio
- Dados enviados (XML)
- Protocolo retornado
- Status final
Chave de acesso e número da NF (em caso de sucesso)
- Mensagem de erro (em caso de falha)

### Notificação por E-mail

Ao final de cada execução, enviar e-mail com:

- Resumo: quantas notas foram emitidas com sucesso, quantas falharam
- Para cada nota com sucesso: nome do cliente, número da NF, link do PDF
- Para cada falha: nome do cliente, mensagem de erro

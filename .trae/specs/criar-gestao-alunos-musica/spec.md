# Gestão de Alunos de Música Spec

## Why
Controlar alunos, conteúdos (vídeos), presença/consumo e financeiro em um único sistema, com uma área do professor (admin) e uma área dos alunos, com visual simples e moderno e deploy em VPS Ubuntu.

## What Changes
- Criar um novo projeto em `e:\projetos\alan-correia-aulas\` com front e back.
- Implementar autenticação com email e senha e controle de acesso por perfil (ADMIN/PROFESSOR e ALUNO).
- Implementar cadastro de alunos com dados básicos e campos financeiros para mensalidade fixa.
- Implementar “show do aluno” com:
  - resumo de tempo desde a data de início
  - resumo financeiro (mensalidade, vencimento, status em dia/em atraso)
  - histórico de vídeos assistidos
- Implementar upload e gestão de vídeos (armazenamento em disco na VPS).
- Implementar planos de estudo vinculados ao aluno, com sequência ordenada de vídeos.
- Registrar quais vídeos cada aluno assistiu (logs e status/progresso).
- Implementar dashboard principal do admin com métricas diárias e gerais.

## Impact
- Affected specs: autenticação, autorização (RBAC), CRUD de domínio (alunos/planos/vídeos), upload/stream, métricas/analytics, UI admin, UI aluno, deploy VPS.
- Affected code: novo código-base em `e:\projetos\alan-correia-aulas\` (front, back, banco, migrações, infraestrutura).

## ADDED Requirements
### Requirement: Stack e execução local
O sistema SHALL ser desenvolvido com:
- Banco de dados: PostgreSQL.
- Backend: Node.js + TypeScript (API HTTP).
- Frontend: aplicação web responsiva em TypeScript.

O sistema SHALL oferecer execução local com PostgreSQL e variáveis de ambiente documentadas (ex.: `.env.example`).

#### Scenario: Desenvolvedor sobe ambiente
- **WHEN** o desenvolvedor inicia o projeto localmente
- **THEN** o banco PostgreSQL fica acessível e a aplicação permite login (admin e aluno) após configuração mínima.

### Requirement: Autenticação e perfis
O sistema SHALL autenticar usuários via email e senha.
O sistema SHALL suportar perfis no mínimo: `ADMIN` (professor) e `STUDENT` (aluno).
O sistema SHALL restringir rotas e dados conforme o perfil.

#### Scenario: Login válido
- **WHEN** um usuário informa email e senha corretos
- **THEN** o sistema cria uma sessão autenticada e redireciona para a área do perfil.

#### Scenario: Acesso negado
- **WHEN** um aluno tenta acessar uma funcionalidade restrita ao admin
- **THEN** o sistema nega o acesso.

### Requirement: Cadastro de alunos
O sistema SHALL permitir ao admin criar, editar, listar e inativar alunos.
O cadastro SHALL incluir dados básicos, no mínimo:
- nome
- email (para login)
- telefone (opcional)
- data de início (para cálculo de “tempo comigo”)

#### Scenario: Admin cadastra aluno
- **WHEN** o admin cria um aluno com dados obrigatórios
- **THEN** o aluno aparece na listagem e passa a ter credenciais para login (email + senha).

### Requirement: Financeiro (mensalidade fixa)
O sistema SHALL suportar mensalidade fixa por aluno.
O sistema SHALL armazenar e calcular:
- valor da mensalidade
- data de vencimento (ou próximo vencimento)
- status financeiro: “em dia” quando o próximo vencimento não está no passado; “em atraso” quando o próximo vencimento está no passado
- lançamentos de pagamento (opcional no MVP) ou marcação de pagamento do mês

#### Scenario: Aluno em atraso
- **WHEN** o próximo vencimento do aluno é anterior à data atual
- **THEN** o aluno é classificado como “em atraso” no dashboard e no show do aluno.

### Requirement: Upload e catálogo de vídeos
O sistema SHALL permitir ao admin fazer upload de vídeos de aulas para o servidor (disco na VPS) e gerenciar metadados (título/descrição).
O sistema SHALL armazenar metadados no banco e o caminho do arquivo no servidor.
O sistema SHALL impedir acesso não autorizado aos arquivos de vídeo.

#### Scenario: Admin envia vídeo
- **WHEN** o admin faz upload de um vídeo válido
- **THEN** o vídeo fica disponível para vinculação em um plano de estudos.

### Requirement: Planos de estudos com sequência ordenada
O sistema SHALL permitir ao admin criar planos de estudos e definir uma sequência ordenada de vídeos.
O sistema SHALL permitir vincular (atribuir) um plano a um aluno.
O sistema SHALL permitir reordenar os itens do plano preservando a ordem.

#### Scenario: Admin monta plano ordenado
- **WHEN** o admin cria um plano com N vídeos e define a ordem
- **THEN** o aluno visualiza o plano com os vídeos na mesma ordem.

### Requirement: Registro de vídeos assistidos
O sistema SHALL registrar eventos de consumo do aluno para os vídeos do plano (ex.: iniciou/assistiu/terminou, progresso).
O sistema SHALL permitir ao admin visualizar no show do aluno o histórico de vídeos assistidos.

#### Scenario: Aluno assiste vídeo
- **WHEN** o aluno assiste um vídeo do plano
- **THEN** o sistema registra a atividade e atualiza o status do vídeo (ex.: “assistido”/progresso).

### Requirement: Dashboard do admin
O sistema SHALL exibir no dashboard do admin, no mínimo:
- quantos alunos assistiram hoje (distintos)
- quantos vídeos cadastrados (total)
- quantos alunos ativos
- quantos alunos em dia
- quantos alunos em atraso

#### Scenario: Admin abre dashboard
- **WHEN** o admin acessa a página inicial
- **THEN** as métricas são calculadas e exibidas com base no banco.

### Requirement: Área do aluno
O sistema SHALL oferecer uma área para o aluno:
- visualizar o plano atribuído
- assistir vídeos na ordem
- acompanhar status (assistido/progresso)

#### Scenario: Aluno acessa seu plano
- **WHEN** o aluno entra na área do aluno
- **THEN** ele vê seu plano e consegue reproduzir os vídeos atribuídos.

### Requirement: Deploy em VPS Ubuntu
O sistema SHALL suportar deploy em VPS Ubuntu com PostgreSQL e armazenamento de vídeos em disco, com configurações via variáveis de ambiente.

#### Scenario: Publicação na VPS
- **WHEN** o projeto é configurado com variáveis e executado na VPS
- **THEN** admin e alunos conseguem acessar via navegador e assistir vídeos com controle de acesso.

## MODIFIED Requirements
(N/A)

## REMOVED Requirements
(N/A)

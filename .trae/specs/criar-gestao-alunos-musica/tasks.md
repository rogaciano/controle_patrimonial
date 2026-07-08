# Tasks
- [x] Task 1: Inicializar o novo projeto em `e:\projetos\alan-correia-aulas\`
  - [x] Definir estrutura (monorepo ou pastas separadas) para `backend/` e `frontend/`
  - [x] Configurar TypeScript, lint/format e scripts básicos (dev/build/test)
  - [x] Adicionar `.env.example` e documentação mínima de setup

- [x] Task 2: Provisionar PostgreSQL e modelagem inicial
  - [x] Criar configuração de conexão e migrações
  - [x] Modelar tabelas/coleções para: usuários, alunos, vídeos, planos, itens do plano, vínculo aluno-plano, logs de consumo e financeiro (mensalidade/vencimento)
  - [x] Criar seed para usuário ADMIN inicial

- [x] Task 3: Implementar autenticação e RBAC (ADMIN/STUDENT)
  - [x] Endpoints/rotas de login/logout e manutenção de sessão/token
  - [x] Proteção de rotas e checagem de perfil
  - [x] Fluxo para admin criar aluno com credenciais (senha inicial) e aluno trocar senha

- [x] Task 4: Implementar CRUD de alunos + status financeiro
  - [x] CRUD (listar/criar/editar/inativar) de alunos
  - [x] Cálculo “tempo comigo” a partir da data de início
  - [x] Regra de “em dia” vs “em atraso” com base no próximo vencimento

- [x] Task 5: Implementar catálogo de vídeos (upload em disco) e streaming com autorização
  - [x] Upload (multipart) e persistência de metadados no banco
  - [x] Armazenamento em diretório configurável por env
  - [x] Endpoint/rota de reprodução/stream protegido por autenticação

- [x] Task 6: Implementar planos de estudo e vínculo com aluno
  - [x] CRUD de planos
  - [x] CRUD de itens do plano com ordenação (reordenação e persistência)
  - [x] Atribuição de plano a aluno

- [x] Task 7: Implementar registro de vídeos assistidos
  - [x] Endpoint/rota para registrar progresso/assistido por aluno
  - [x] Consultas para histórico de consumo no “show do aluno”
  - [x] Métricas “alunos assistiram hoje” (distintos) e totais relevantes

- [x] Task 8: Implementar UI do admin (visual simples e moderno)
  - [x] Tela de login
  - [x] Dashboard com métricas
  - [x] Listagem e cadastro de alunos
  - [x] Show do aluno (tempo comigo, financeiro, histórico)
  - [x] Gestão de vídeos e planos (inclui ordenação)

- [x] Task 9: Implementar UI do aluno
  - [x] Tela de login
  - [x] Visualização do plano atribuído com sequência ordenada
  - [x] Player de vídeo e atualização de progresso/assistido

- [x] Task 10: Validação e prontidão de deploy
  - [x] Testes mínimos (unitários e/ou integração) para regras de financeiro, RBAC e métricas
  - [x] Smoke test manual documentado (login admin, criar aluno, upload vídeo, criar plano, aluno assiste, dashboard atualiza)
  - [x] Artefatos de deploy (ex.: docker compose/systemd/nginx) alinhados com VPS Ubuntu e storage em disco

# Task Dependencies
- Task 2 depende de Task 1
- Task 3 depende de Task 2
- Task 4 depende de Task 3
- Task 5 depende de Task 3 e Task 2
- Task 6 depende de Task 5
- Task 7 depende de Task 6
- Task 8 depende de Task 3, Task 4, Task 6 e Task 7
- Task 9 depende de Task 3, Task 6 e Task 7
- Task 10 depende de Task 8 e Task 9

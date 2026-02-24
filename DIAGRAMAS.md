# Documentação de Diagramas - Controle Patrimonial

Abaixo estão as representações visuais em diagramas documentando a Arquitetura de Dados e o Fluxo de Informação do sistema.

## 1. Diagrama Entidade-Relacionamento (ERD)
Este diagrama ilustra como as tabelas do banco de dados se relacionam entre si, incluindo as chaves estrangeiras (Foreign Keys) e as entidades do sistema.

```mermaid
erDiagram
    %% Core App
    Empresa {
        int id PK
        string cnpj UK
        string nome_razao
        string nome_fantasia
        boolean matriz
        string cidade
        string uf
        string endereco
    }

    %% Patrimonio App
    CategoriaContabil {
        int id PK
        int parent_id FK "Auto-relacionamento"
        string codigo UK
        string nome
        decimal taxa_depreciacao_anual
        int vida_util_padrao_meses
    }

    CentroCusto {
        int id PK
        int empresa_id FK
        string codigo UK
        string nome
        string departamento
    }

    LocalFisico {
        int id PK
        int empresa_id FK
        string codigo UK
        string nome
        string tipo
    }

    Responsavel {
        int id PK
        int empresa_id FK
        string matricula UK
        string cpf UK
        string nome
        string email
    }

    Ativo {
        int id PK
        int empresa_id FK
        int categoria_id FK
        int centro_custo_id FK
        int local_fisico_id FK
        int responsavel_id FK
        string numero_tombamento UK
        string descricao_detalhada
        decimal valor_aquisicao
        date data_aquisicao
        string status
    }

    AtivoImagem {
        int id PK
        int ativo_id FK
        string imagem
        boolean principal
    }

    Movimentacao {
        int id PK
        int ativo_id FK
        int local_origem_id FK
        int local_destino_id FK
        int responsavel_origem_id FK
        int responsavel_destino_id FK
        datetime data_movimentacao
        string status
    }

    Inventario {
        int id PK
        int empresa_id FK
        int responsavel_id FK
        string codigo UK
        date data_inicio
        string status
    }

    InventarioItem {
        int id PK
        int inventario_id FK
        int ativo_id FK
        int local_encontrado_id FK
        int responsavel_encontrado_id FK
        string status
    }

    InventarioItemEvidencia {
        int id PK
        int item_id FK
        string foto
    }

    InventarioSobra {
        int id PK
        int inventario_id FK
        int local_encontrado_id FK
        int responsavel_encontrado_id FK
        string descricao_bem
    }

    %% Relacionamentos
    Empresa ||--o{ CentroCusto : "Possui"
    Empresa ||--o{ LocalFisico : "Possui"
    Empresa ||--o{ Responsavel : "Possui"
    Empresa ||--o{ Ativo : "Controla"
    Empresa ||--o{ Inventario : "Realiza"

    CategoriaContabil ||--o{ CategoriaContabil : "Subcategoria"
    CategoriaContabil ||--o{ Ativo : "Classifica"
    
    CentroCusto ||--o{ Ativo : "Aloca"
    LocalFisico ||--o{ Ativo : "Armazena"
    Responsavel ||--o{ Ativo : "Guarda"

    Ativo ||--o{ AtivoImagem : "Tem fotos"
    Ativo ||--o{ Movimentacao : "Sofre"
    LocalFisico ||--o{ Movimentacao : "Origem/Destino"
    Responsavel ||--o{ Movimentacao : "Origem/Destino"

    Responsavel ||--o{ Inventario : "Responsável Técnico"
    Inventario ||--o{ InventarioItem : "Contém"
    Inventario ||--o{ InventarioSobra : "Registra Sobras"
    
    Ativo ||--o{ InventarioItem : "Verificado em"
    LocalFisico ||--o{ InventarioItem : "Localizado em"
    Responsavel ||--o{ InventarioItem : "Em posse de"

    InventarioItem ||--o{ InventarioItemEvidencia : "Comprovações/Avarias"
```

---

## 2. Diagrama de Fluxo de Dados (DFD) - Nível 1
Este diagrama representa as principais interações do usuário com o sistema e os processos de fluxo de informação e guarda de dados na base.

```mermaid
graph TD
    %% Entidades Externas
    Usuario((Usuário / Gerente))

    %% Processos (Ações do Sistema)
    proc1(1. Gestão Cadastral\nEmpresas, Locais,\nCustos e Responsáveis)
    proc2(2. Gestão de Ativos\nAquisição, Baixa\ne Tombamento)
    proc3(3. Movimentação\nTransferências\nde Posse/Local)
    proc4(4. Execução de Inventário\nAuditoria e Conciliação)
    proc5(5. Geração de Dashboards\ne Relatórios)

    %% Banco de Dados (Data Stores)
    db1[(Cadastros Base)]
    db2[(Patrimônio/Ativos)]
    db3[(Histórico de\nMovimentações)]
    db4[(Inventários\ne Auditorias)]

    %% Fluxos de Informação
    Usuario -->|Fornece dados cadastrais| proc1
    proc1 -->|Grava Tabelas Auxiliares| db1
    proc1 -.->|Lê Cadastros| Usuario

    Usuario -->|Cadastra Ativo/Baixa| proc2
    db1 -->|Fornece Categoria/Local/Empresa| proc2
    proc2 -->|Grava/Atualiza Ativo| db2

    Usuario -->|Solicita Transferência| proc3
    db2 -->|Consulta Status/Local Atual| proc3
    proc3 -->|Atualiza Novo Local/Resp| db2
    proc3 -->|Registra Histórico| db3
    
    Usuario -->|Inicia/Fecha Inventário| proc4
    db2 -->|Fornece Lista de Ativos Esperados| proc4
    proc4 -->|Registra Sobras/Faltas/Avarias| db4
    proc4 -.->|Informa Divergências| Usuario

    Usuario -->|Solicita Visão Geral| proc5
    db1 -->|Filtro de Empresa| proc5
    db2 -->|Consolida Valores/Quantidades| proc5
    db3 -->|Gera Timeline| proc5
    proc5 -->|Exibe Gráficos e Tabelas| Usuario

    %% Estilização do DFD
    classDef external fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef process fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
    classDef datastore fill:#fef3c7,stroke:#f59e0b,stroke-width:2px;

    class Usuario external;
    class proc1,proc2,proc3,proc4,proc5 process;
    class db1,db2,db3,db4 datastore;
```

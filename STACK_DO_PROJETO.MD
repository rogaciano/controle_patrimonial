# 🚀 PROMPT INICIAL - PROJETO [NOME_DO_PROJETO] (Django)

## 📋 CONTEXTO
Criar um sistema ERP modular para gestão de [processo/negócio específico], inspirado no modelo de sucesso do Rota do Mar (sistema de gestão de produção têxtil).

---

## 🏗️ STACK TECNOLÓGICO OBRIGATÓRIO

### Backend
- **Python 3.12+** com type hints
- **Django 5.x** (framework principal)
- **django-allauth 0.63+** (autenticação completa)
- **django-auditlog** (auditoria de ações)
- **WeasyPrint** ou **xhtml2pdf** (relatórios PDF)
- **django-filter** (filtros avançados em listagens)
- **django-widget-tweaks** (customização de forms no template)
- **SQLite/PostgreSQL** (banco de dados)

### Frontend
- **Vite 6.x** via **django-vite** (build tool integrado ao Django)
- **Tailwind CSS 3.x** com modo escuro (`darkMode: 'class'`)
- **Alpine.js 3.x** (interatividade leve)
- **jQuery 3.6+** (para componentes complexos como Select2)
- **Select2** (dropdowns avançados)
- **Chart.js 4.x** (gráficos e dashboards)
- **Django Templates** (templating engine nativa)

### 🎨 Design Tokens (Identidade Visual Centralizada)

> **REGRA:** Todas as cores, fontes e espaçamentos DEVEM ser definidos como tokens (CSS Custom Properties).
> Para mudar a identidade visual inteira, basta alterar UM arquivo: `static/css/tokens.css`.

#### Arquivo `static/css/tokens.css` (FONTE ÚNICA DE VERDADE)
```css
/* ========================================
   DESIGN TOKENS - IDENTIDADE VISUAL
   Altere APENAS este arquivo para trocar
   toda a paleta de cores do sistema.
   ======================================== */

:root {
    /* --- Cores Primárias --- */
    --color-primary-50: #f0f9ff;
    --color-primary-100: #e0f2fe;
    --color-primary-200: #bae6fd;
    --color-primary-300: #7dd3fc;
    --color-primary-400: #38bdf8;
    --color-primary-500: #0ea5e9;
    --color-primary-600: #0284c7;
    --color-primary-700: #0369a1;
    --color-primary-800: #075985;
    --color-primary-900: #0c4a6e;
    --color-primary-950: #082f49;

    /* --- Cores Secundárias --- */
    --color-secondary-50: #f8fafc;
    --color-secondary-100: #f1f5f9;
    --color-secondary-200: #e2e8f0;
    --color-secondary-300: #cbd5e1;
    --color-secondary-400: #94a3b8;
    --color-secondary-500: #64748b;
    --color-secondary-600: #475569;
    --color-secondary-700: #334155;
    --color-secondary-800: #1e293b;
    --color-secondary-900: #0f172a;
    --color-secondary-950: #020617;

    /* --- Cores Semânticas --- */
    --color-success: #10b981;
    --color-warning: #f59e0b;
    --color-danger: #ef4444;
    --color-info: #3b82f6;

    /* --- Tipografia --- */
    --font-family: 'Figtree', sans-serif;
    --font-size-base: 1rem;

    /* --- Espaçamento --- */
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-2xl: 1.5rem;
}
```

#### Integração com Tailwind (`tailwind.config.js`)
```javascript
// tailwind.config.js - Consome tokens CSS, NÃO hardcoda cores
colors: {
    primary: {
        50: 'var(--color-primary-50)',
        100: 'var(--color-primary-100)',
        200: 'var(--color-primary-200)',
        300: 'var(--color-primary-300)',
        400: 'var(--color-primary-400)',
        500: 'var(--color-primary-500)',
        600: 'var(--color-primary-600)',
        700: 'var(--color-primary-700)',
        800: 'var(--color-primary-800)',
        900: 'var(--color-primary-900)',
        950: 'var(--color-primary-950)',
    },
    secondary: {
        50: 'var(--color-secondary-50)',
        // ... mesma estrutura
    }
}
```

#### No `static/css/app.css`
```css
/* Importar tokens ANTES do Tailwind */
@import './tokens.css';
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Classes utilitárias que consomem tokens */
@layer components {
    .btn-primary {
        @apply bg-primary-600 hover:bg-primary-700 text-white
               rounded-lg px-4 py-2 font-medium transition-colors;
    }
    .btn-ghost-primary {
        @apply text-primary-600 hover:bg-primary-50
               dark:hover:bg-primary-900/20 rounded-lg px-3 py-2
               font-medium transition-colors;
    }
    .form-input {
        @apply block w-full border-gray-300 dark:border-slate-600
               bg-white dark:bg-slate-800 text-gray-900 dark:text-white
               focus:border-primary-500 focus:ring-primary-500
               rounded-md shadow-sm;
    }
    .form-label {
        @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1;
    }
    .form-error {
        @apply mt-1 text-sm text-red-600;
    }
}
```

> ✅ **Para trocar a identidade visual:** edite APENAS `tokens.css`. Todo o sistema atualiza automaticamente.
> ❌ **PROIBIDO:** Usar cores hardcoded em templates (`bg-[#0ea5e9]`). Use SEMPRE classes Tailwind que referenciam tokens (`bg-primary-600`).

---

## 📦 DEFINIÇÃO DO PROJETO

<!-- ============================================================
   INSTRUÇÕES DE PREENCHIMENTO:
   
   Esta seção é OBRIGATÓRIA. Preencha TODOS os campos abaixo
   com as informações específicas do seu projeto.
   
   DICA: Quanto mais detalhado, melhor o resultado da IA.
   Não use termos vagos como "gerenciar coisas".
   Seja específico: "Cadastrar produtos têxteis com referência,
   composição, largura e preço por metro".
   ============================================================ -->

### Nome do Projeto
<!-- Substitua pelo nome real -->
**[NOME_DO_PROJETO]**

### Descrição
<!-- 2-3 frases explicando O QUE o sistema faz e PARA QUEM -->
Sistema para [descreva o processo/negócio] destinado a [público-alvo].
Permite [principais ações que os usuários executam].

### Módulos do Sistema
<!-- Liste TODOS os módulos. Marque com ⭐ os prioritários (MVP). -->

| # | Módulo | Descrição | Prioridade |
|---|--------|-----------|------------|
| 1 | ⭐ [Ex: Cadastro de Produtos] | [O que faz este módulo] | MVP |
| 2 | ⭐ [Ex: Orçamentos] | [O que faz] | MVP |
| 3 | [Ex: Relatórios] | [O que faz] | Fase 2 |
| 4 | [Ex: Nota Fiscal] | [O que faz] | Fase 3 |

### Papéis de Usuário (Permissões)
<!-- Defina QUEM pode fazer O QUÊ. Isso impacta views e permissions. -->

| Papel | Pode acessar | Restrições |
|-------|-------------|------------|
| Admin | Tudo | Nenhuma |
| [Ex: Gerente] | [Módulos X, Y, Z] | [Não pode excluir registros] |
| [Ex: Vendedor] | [Apenas orçamentos] | [Somente leitura em cadastros] |
| [Ex: Produção] | [Ordens de produção] | [Sem acesso financeiro] |

### Regras de Negócio
<!-- Liste as regras que o SISTEMA deve impor automaticamente.
     Formato: "QUANDO [condição], ENTÃO [ação], SENÃO [alternativa]" -->

1. [Ex: QUANDO um orçamento for aprovado, ENTÃO gerar ordem de produção automaticamente]
2. [Ex: QUANDO estoque ficar abaixo de 10 unidades, ENTÃO notificar o gestor]
3. [Ex: QUANDO preço de venda < preço de custo, ENTÃO bloquear e exigir justificativa]
4. ...

### Fluxos Principais
<!-- Descreva o caminho que o usuário percorre nas funcionalidades principais.
     Use setas → para indicar o fluxo. -->

1. **Fluxo de [Ex: Orçamento]:**
   Login → Dashboard → Novo Orçamento → Selecionar Cliente → Adicionar Itens → Calcular Total → Salvar → Enviar por Email/WhatsApp

2. **Fluxo de [Ex: Produção]:**
   [Descreva o passo a passo]

### Integrações (se houver)
<!-- Marque com ✅ as que precisa, ❌ as que não precisa -->

- [ ] WhatsApp (envio de orçamentos/notificações)
- [ ] Email (SMTP para notificações)
- [ ] API de CEP (ViaCEP para auto-completar endereço)
- [ ] Nota Fiscal Eletrônica (NF-e)
- [ ] Gateway de Pagamento (Stripe/PagSeguro/Pix)
- [ ] Importação/Exportação Excel
- [ ] [Outra integração específica]

### ❌ NÃO FAÇA (Anti-patterns)
<!-- Liste o que a IA NÃO deve fazer neste projeto -->

- [ ] Não criar API REST separada — usar server-side rendering (Django Templates)
- [ ] Não usar SPA (React/Vue) — manter Django Templates + Alpine.js
- [ ] Não criar formulários genéricos — cada form deve ser customizado
- [ ] [Adicione suas restrições específicas]

---

## 🗃️ MODELAGEM DE DADOS

<!-- ============================================================
   INSTRUÇÕES DE PREENCHIMENTO:

   Para cada tabela do sistema, preencha o modelo abaixo.
   
   COMO DEFINIR CAMPOS:
   1. Pense em "que informações preciso guardar sobre [entidade]?"
   2. Para cada campo, defina: nome, tipo, se é obrigatório, e regras
   3. Use os TIPOS PADRÃO listados abaixo
   4. Campos com FORMATAÇÃO AUTOMÁTICA (ver lista) não precisam de
      especificação extra — o sistema já aplicará as máscaras/validações

   TIPOS DE CAMPO DISPONÍVEIS (Django):
   - CharField(N)        → Texto com N caracteres max
   - TextField           → Texto longo (descrições, observações)
   - IntegerField        → Número inteiro
   - DecimalField(P,S)   → Decimal com P dígitos e S casas
   - BooleanField        → Sim/Não (checkbox)
   - DateField           → Data (dd/mm/aaaa)
   - DateTimeField       → Data e hora
   - choices(A,B,C)      → Lista fixa de opções (TextChoices)
   - JSONField           → Dados flexíveis (características extras)
   - FileField           → Upload de arquivo
   - ImageField          → Upload de imagem (com thumbnail automático)

   RELACIONAMENTOS:
   - ForeignKey(Model)         → "pertence a" (muitos-para-um)
   - OneToOneField(Model)      → "um-para-um"
   - ManyToManyField(Model)    → "muitos-para-muitos"
   - ManyToManyField(through)  → M2M com campos extras na pivot
   ============================================================ -->

### 🔄 Formatações Automáticas (aplicadas sem precisar pedir)

> **REGRA:** Todo campo que se enquadre nos tipos abaixo DEVE ser
> implementado automaticamente com máscara, validação e formatação.
> Não é necessário especificar — o dev DEVE aplicar por padrão.

| Tipo de Campo | Máscara/Formato | Validação Automática | Armazenamento |
|---------------|----------------|---------------------|---------------|
| **Telefone** | `(99) 99999-9999` | Aceitar 10-11 dígitos, DDD válido | Apenas números |
| **CEP** | `99999-999` | 8 dígitos + auto-completar via ViaCEP | Apenas números |
| **CPF** | `999.999.999-99` | Validar dígitos verificadores | Apenas números |
| **CNPJ** | `99.999.999/9999-99` | Validar dígitos verificadores | Apenas números |
| **Email** | Lowercase automático | Formato válido (RFC 5322) | Lowercase |
| **Dinheiro (R$)** | `R$ 1.234,56` | Decimal positivo, 2 casas | `DecimalField(10,2)` |
| **Porcentagem** | `99,99%` | 0-100 com 2 casas | `DecimalField(5,2)` |
| **Data** | `dd/mm/aaaa` | Data válida, calendário picker | `DateField` |
| **Hora** | `HH:mm` | Hora válida (00:00-23:59) | `TimeField` |
| **Placa veículo** | `AAA-9A99` (Mercosul) | Formato antigo ou Mercosul | Uppercase |
| **RG** | Livre (varia por estado) | Máximo 14 caracteres | String limpa |
| **URL/Site** | `https://...` | Validar formato URL | `URLField` |

#### Implementação padrão (Django):
```python
# apps/core/validators.py - Validadores reutilizáveis
import re
from django.core.exceptions import ValidationError


def validar_cpf(value: str) -> None:
    cpf = re.sub(r'\D', '', value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if int(cpf[i]) != digito:
            raise ValidationError('CPF inválido.')


def validar_cnpj(value: str) -> None:
    cnpj = re.sub(r'\D', '', value)
    if len(cnpj) != 14:
        raise ValidationError('CNPJ inválido.')


def validar_telefone(value: str) -> None:
    telefone = re.sub(r'\D', '', value)
    if len(telefone) not in (10, 11):
        raise ValidationError('Telefone deve ter 10 ou 11 dígitos.')


def validar_cep(value: str) -> None:
    cep = re.sub(r'\D', '', value)
    if len(cep) != 8:
        raise ValidationError('CEP deve ter 8 dígitos.')
```

```python
# No Model - usar validators
from apps.core.validators import validar_cpf, validar_cnpj, validar_telefone, validar_cep

class Cliente(BaseModel):
    telefone = models.CharField(max_length=11, blank=True, validators=[validar_telefone])
    cep = models.CharField(max_length=8, blank=True, validators=[validar_cep])
    cpf = models.CharField(max_length=11, blank=True, validators=[validar_cpf])
    cnpj = models.CharField(max_length=14, blank=True, validators=[validar_cnpj])
    email = models.EmailField(blank=True)  # Django já valida formato
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
```

```html
<!-- No Template - máscaras via Alpine.js + x-mask -->
<input x-mask="(99) 99999-9999" name="telefone" class="form-input">
<input x-mask="99999-999" name="cep" @blur="buscarCep($el.value)" class="form-input">
<input x-mask="999.999.999-99" name="cpf" class="form-input">
```

```javascript
// Função global para busca automática de CEP
async function buscarCep(cep) {
    cep = cep.replace(/\D/g, '');
    if (cep.length !== 8) return;
    const resp = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
    const data = await resp.json();
    if (!data.erro) {
        document.querySelector('[name="logradouro"]').value = data.logradouro;
        document.querySelector('[name="bairro"]').value = data.bairro;
        document.querySelector('[name="cidade"]').value = data.localidade;
        document.querySelector('[name="uf"]').value = data.uf;
    }
}
```

### 📋 Tabelas do Sistema

<!-- ============================================================
   MODELO PARA COPIAR/COLAR PARA CADA TABELA:
   
   Copie o bloco abaixo e preencha para cada entidade do sistema.
   Remova os exemplos e substitua pelos seus campos reais.
   ============================================================ -->

#### Tabela: `[nome_da_tabela]` (Ex: `produtos`)
<!-- Descrição: [Para que serve esta tabela] -->

| Campo | Tipo | Obrigatório | Regras/Observações |
|-------|------|:-----------:|-------------------|
| `id` | auto | ✅ | PK auto-incremento (incluído automaticamente) |
| `[campo_1]` | CharField(100) | ✅ | [Ex: Único, usado como identificador visual] |
| `[campo_2]` | CharField(255) | ✅ | [Ex: Nome descritivo do item] |
| `[campo_fk]` | ForeignKey(Model) | ✅ | [Ex: Categoria do produto] |
| `[campo_valor]` | DecimalField(10,2) | ❌ | [Ex: Preço de custo, default 0] |
| `[campo_data]` | DateField | ❌ | [Ex: Data prevista de entrega] |
| `[campo_status]` | choices(ativo,inativo,rascunho) | ✅ | [Ex: Default "rascunho"] |
| `[campo_obs]` | TextField | ❌ | [Ex: Observações livres] |
| `[campo_arquivo]` | FileField | ❌ | [Ex: PDF da ficha técnica, max 5MB] |
| `[campo_m2m]` | ManyToManyField(Model) | ❌ | [Ex: Tecidos com through table "consumo"] |
| `criado_em` | DateTimeField | ✅ | auto_now_add=True |
| `atualizado_em` | DateTimeField | ✅ | auto_now=True |
| `ativo` | BooleanField | ✅ | Soft delete, default=True |

<!-- REPITA O BLOCO ACIMA PARA CADA TABELA DO SISTEMA -->

<!-- Exemplo preenchido para referência:

#### Tabela: `clientes`
| Campo | Tipo | Obrigatório | Regras/Observações |
|-------|------|:-----------:|-------------------|
| `id` | auto | ✅ | PK |
| `razao_social` | CharField(255) | ✅ | Nome completo ou razão social |
| `nome_fantasia` | CharField(255) | ❌ | Apelido comercial |
| `tipo_pessoa` | choices(PF,PJ) | ✅ | Pessoa Física ou Jurídica |
| `cpf_cnpj` | CharField(14) | ✅ | ⚡ FORMATAÇÃO AUTOMÁTICA (CPF ou CNPJ) |
| `email` | EmailField | ❌ | ⚡ FORMATAÇÃO AUTOMÁTICA |
| `telefone` | CharField(11) | ❌ | ⚡ FORMATAÇÃO AUTOMÁTICA |
| `cep` | CharField(8) | ❌ | ⚡ FORMATAÇÃO AUTOMÁTICA + ViaCEP |
| `logradouro` | CharField(255) | ❌ | Preenchido automaticamente pelo CEP |
| `numero` | CharField(10) | ❌ | |
| `complemento` | CharField(100) | ❌ | |
| `bairro` | CharField(100) | ❌ | Preenchido automaticamente pelo CEP |
| `cidade` | CharField(100) | ❌ | Preenchido automaticamente pelo CEP |
| `uf` | CharField(2) | ❌ | Preenchido automaticamente pelo CEP |
| `observacoes` | TextField | ❌ | |
| `vendedor` | ForeignKey(User) | ❌ | Vendedor responsável |
| `criado_em` | DateTimeField | ✅ | auto_now_add=True |
| `atualizado_em` | DateTimeField | ✅ | auto_now=True |
| `ativo` | BooleanField | ✅ | Soft delete, default=True |

⚡ = Campo com formatação automática (não precisa especificar máscara)
-->

---

## 🏛️ ARQUITETURA DO SISTEMA

### 1. ESTRUTURA DE DIRETÓRIOS
```
projeto/
├── config/                     # Projeto Django (settings, urls, wsgi)
│   ├── settings/
│   │   ├── base.py             # Settings compartilhadas
│   │   ├── dev.py              # Settings de desenvolvimento
│   │   └── prod.py             # Settings de produção
│   ├── urls.py                 # URLs raiz
│   └── wsgi.py
├── apps/                       # Apps Django organizadas por domínio
│   ├── core/                   # App base (mixins, utils, templatetags)
│   │   ├── mixins.py           # AuditMixin, SoftDeleteMixin, etc.
│   │   ├── templatetags/       # Tags e filtros customizados
│   │   └── utils.py            # Funções auxiliares
│   ├── accounts/               # Autenticação e perfis de usuário
│   │   ├── models.py
│   │   ├── views.py
│   │   └── forms.py
│   └── [modulo]/               # Cada módulo de negócio é uma app
│       ├── models.py
│       ├── views.py
│       ├── forms.py
│       ├── urls.py
│       ├── admin.py
│       ├── filters.py          # django-filter classes
│       ├── services.py         # [Opcional] Lógica de negócio complexa
│       └── templates/[modulo]/ # Templates específicos do módulo
│           ├── produto_list.html
│           ├── produto_detail.html  # 👁️ Ficha completa com relacionamentos
│           ├── produto_form.html
│           └── partials/       # ⚠️ PARTIALS OBRIGATÓRIAS
│               ├── _filters.html
│               ├── _table.html
│               ├── _detail_info.html     # Dados principais da ficha
│               ├── _detail_relations.html # Tabs/seções de relacionamentos
│               ├── _form_fields.html
│               ├── _form_scripts.html
│               └── _actions.html
├── templates/                  # Templates globais
│   ├── base.html               # Layout principal com dark mode
│   ├── components/             # Componentes reutilizáveis (includes)
│   │   ├── _card_stat.html
│   │   ├── _pagination.html
│   │   ├── _flash_messages.html
│   │   └── _confirm_modal.html
│   └── includes/
│       └── _navigation.html
├── static/                     # Arquivos estáticos (se não usar Vite)
│   ├── css/
│   │   └── app.css             # Imports Tailwind + custom CSS
│   └── js/
│       └── app.js              # Alpine.js + scripts globais
├── media/                      # Uploads de usuários
├── requirements/
│   ├── base.txt                # Dependências compartilhadas
│   ├── dev.txt                 # Dependências de desenvolvimento
│   └── prod.txt                # Dependências de produção
└── manage.py
```

### 2. ⚠️ REGRA DE PARTIALS (OBRIGATÓRIO)

> **NUNCA crie arquivos de template com mais de 150 linhas.**
> Se um arquivo ultrapassar esse limite, ele DEVE ser decomposto em partials via `{% include %}`.

#### Princípios:
1. **Prefixo `_`**: Toda partial começa com underscore (`_filtros.html`)
2. **Uma responsabilidade**: Cada partial faz UMA coisa (filtros, tabela, form, scripts)
3. **Reutilização**: Partials usadas em mais de um módulo vão em `templates/components/`
4. **Sem lógica pesada**: Partials contêm apenas HTML/Django Template. Lógica fica na View
5. **Contexto explícito**: Sempre passe variáveis com `{% include %} with` quando necessário

#### Decomposição padrão de um CRUD:

| Arquivo | Conteúdo | Limite |
|---------|----------|--------|
| `produto_list.html` | Layout + includes das partials | ~30 linhas |
| `partials/_filters.html` | Barra de filtros/busca | ~40-60 linhas |
| `partials/_table.html` | Tabela de listagem + ações (👁️ Editar ✏️ Excluir 🗑️) | ~60-80 linhas |
| `produto_detail.html` | 👁️ Ficha completa (show) + includes | ~40-60 linhas |
| `partials/_detail_info.html` | Dados principais organizados em grid | ~60-80 linhas |
| `partials/_detail_relations.html` | Tabs/seções com registros relacionados | ~80-120 linhas |
| `produto_form.html` | Layout + include do form | ~20 linhas |
| `partials/_form_fields.html` | Campos do formulário | ~60-100 linhas |
| `partials/_form_scripts.html` | JS específico (Select2, masks) | ~30-50 linhas |
| `components/_card_stat.html` | Card de estatística (global) | ~20 linhas |
| `components/_confirm_modal.html` | Modal de confirmação (global) | ~30 linhas |

#### Exemplo de uso no `produto_list.html`:
```html
{% extends 'base.html' %}

{% block title %}Produtos{% endblock %}

{% block header %}
<header class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        <h2 class="text-xl font-semibold">Produtos</h2>
        <a href="{% url 'produtos:create' %}" class="btn-primary">+ Novo</a>
    </div>
</header>
{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
    {# Filtros #}
    {% include 'produtos/partials/_filters.html' %}

    {# Tabela de resultados #}
    {% include 'produtos/partials/_table.html' with itens=itens %}

    {# Paginação #}
    {% include 'components/_pagination.html' %}
</div>
{% endblock %}
```

#### Exemplo de `partials/_filters.html`:
```html
<div class="glass dark:glass-dark rounded-xl p-4 mb-6">
    <form method="GET" action="{% url 'produtos:list' %}" class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
            <input type="text" name="busca" value="{{ request.GET.busca }}"
                   placeholder="Buscar por referência ou descrição..."
                   class="form-input w-full">
        </div>
        <div>
            <select name="marca" class="form-select w-full select2">
                <option value="">Todas as marcas</option>
                {% for marca in marcas %}
                    <option value="{{ marca.id }}" {% if request.GET.marca == marca.id|stringformat:"d" %}selected{% endif %}>
                        {{ marca.nome }}
                    </option>
                {% endfor %}
            </select>
        </div>
        <div class="flex items-end gap-2">
            <button type="submit" class="btn-primary">Filtrar</button>
            <a href="{% url 'produtos:list' %}" class="btn-ghost-secondary">Limpar</a>
        </div>
    </form>
</div>
```

#### Exemplo de `partials/_form_fields.html`:
```html
{# Campos compartilhados entre create e edit #}
{% load widget_tweaks %}

<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="form-group">
        <label class="form-label">Referência <span class="text-red-500">*</span></label>
        {% render_field form.referencia class="form-input" %}
        {% if form.referencia.errors %}
            {% for error in form.referencia.errors %}
                <p class="form-error">{{ error }}</p>
            {% endfor %}
        {% endif %}
    </div>

    <div class="form-group">
        <label class="form-label">Descrição <span class="text-red-500">*</span></label>
        {% render_field form.descricao class="form-input" %}
        {% if form.descricao.errors %}
            {% for error in form.descricao.errors %}
                <p class="form-error">{{ error }}</p>
            {% endfor %}
        {% endif %}
    </div>

    {# ... demais campos #}
</div>
```

### 3. PADRÕES DE CÓDIGO

#### Models (Exemplo: Produto)
```python
from django.db import models
from django.urls import reverse
from auditlog.registry import auditlog


class BaseModel(models.Model):
    """Mixin base com campos de auditoria."""
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.ativo = False
        self.save(update_fields=['ativo'])


class Produto(BaseModel):
    referencia = models.CharField(max_length=50, unique=True)
    descricao = models.CharField(max_length=255)
    marca = models.ForeignKey(
        'Marca',
        on_delete=models.PROTECT,
        related_name='produtos'
    )
    estilista = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='produtos_estilista'
    )
    status = models.ForeignKey(
        'Status',
        on_delete=models.PROTECT,
        related_name='produtos'
    )
    data_entrega_faccao = models.DateField(null=True, blank=True)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Many-to-Many com campo extra na tabela pivot
    tecidos = models.ManyToManyField(
        'Tecido',
        through='ProdutoTecido',
        related_name='produtos'
    )

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self) -> str:
        return f'{self.referencia} - {self.descricao}'

    def get_absolute_url(self) -> str:
        return reverse('produtos:detail', kwargs={'pk': self.pk})

    @property
    def custo_total(self) -> float:
        return float(self.preco_custo * self.quantidade)

    # QuerySet customizado (equivale aos Scopes do Laravel)
    class ProdutoQuerySet(models.QuerySet):
        def ativos(self):
            return self.filter(ativo=True)

        def por_marca(self, marca_id: int):
            return self.filter(marca_id=marca_id)

    objects = ProdutoQuerySet.as_manager()


class ProdutoTecido(models.Model):
    """Tabela pivot com campo extra."""
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    tecido = models.ForeignKey('Tecido', on_delete=models.CASCADE)
    consumo = models.DecimalField(max_digits=8, decimal_places=3)

    class Meta:
        unique_together = ['produto', 'tecido']


# Registrar para auditoria automática
auditlog.register(Produto)
```

#### Views (Class-Based Views Pattern)
```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django_filters.views import FilterView

from .models import Produto
from .forms import ProdutoForm
from .filters import ProdutoFilter

import logging
logger = logging.getLogger(__name__)


class ProdutoListView(LoginRequiredMixin, FilterView):
    """Listagem com filtros e paginação."""
    model = Produto
    template_name = 'produtos/produto_list.html'
    context_object_name = 'itens'
    paginate_by = 20
    filterset_class = ProdutoFilter

    def get_queryset(self):
        return (
            Produto.objects.ativos()
            .select_related('marca', 'estilista', 'status')
            .order_by('-criado_em')
        )


class ProdutoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Criação com transação e tratamento de erro."""
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/produto_form.html'
    success_url = reverse_lazy('produtos:list')
    success_message = 'Produto criado com sucesso!'

    @transaction.atomic
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            # Relacionamentos many-to-many
            tecidos = self.request.POST.getlist('tecidos')
            if tecidos:
                self.object.tecidos.set(tecidos)
            return response
        except Exception as e:
            logger.error(f'Erro ao criar produto: {e}')
            messages.error(self.request, f'Erro ao criar: {e}')
            return self.form_invalid(form)


class ProdutoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Edição com mesma lógica."""
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/produto_form.html'
    success_url = reverse_lazy('produtos:list')
    success_message = 'Produto atualizado com sucesso!'


class ProdutoDeleteView(LoginRequiredMixin, DeleteView):
    """Exclusão com confirmação."""
    model = Produto
    success_url = reverse_lazy('produtos:list')

    def delete(self, request, *args, **kwargs):
        try:
            messages.success(request, 'Produto excluído com sucesso!')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f'Erro ao excluir: {e}')
            return self.get(request, *args, **kwargs)
```

#### 👁️ PADRÃO DE TELA DE DETALHE (Show/Ficha Completa) - OBRIGATÓRIO

> **REGRA:** Toda entidade principal DEVE ter uma tela de detalhe (show) acessível via ícone de olho (👁️) na listagem.
> A ficha mostra dados completos + registros relacionados em seções/abas.

##### Ações na Listagem (3 ícones por linha):

| Ícone | Ação | View | Descrição |
|-------|------|------|-----------|
| 👁️ Olho | Visualizar | `DetailView` | Ficha completa com relacionamentos |
| ✏️ Lápis | Editar | `UpdateView` | Formulário de edição |
| 🗑️ Lixeira | Excluir | `DeleteView` | Confirmação e exclusão |

##### Estrutura da Ficha de Detalhe:

```
┌─────────────────────────────────────────────┐
│ Header: Título + Badge Status + Botões      │
│         [← Voltar] [✏️ Editar] [🗑️ Excluir] │
├─────────────────────────────────────────────┤
│ Seção 1: Dados Principais (grid 2-3 cols)   │
│   Campo: Valor    |  Campo: Valor           │
│   Campo: Valor    |  Campo: Valor           │
├─────────────────────────────────────────────┤
│ Seção 2: Registros Relacionados (tabs)      │
│ [Tab1: Movimentações] [Tab2: Inventários]   │
│ ┌─────────────────────────────────────────┐ │
│ │ Tabela com registros do relacionamento  │ │
│ │ Data | Descrição | Status | Ações       │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ Seção 3: Timeline / Auditoria (opcional)    │
└─────────────────────────────────────────────┘
```

##### Mapeamento de Relacionamentos por Entidade:

| Entidade | Seções de Relacionamento na Ficha |
|----------|-----------------------------------|
| **Ativo** | Movimentações, Registros de Depreciação, Itens de Inventário |
| **Categoria** | Ativos vinculados (lista com contagem) |
| **Centro de Custo** | Ativos alocados |
| **Local Físico** | Ativos presentes, Movimentações (origem/destino) |
| **Responsável** | Ativos sob responsabilidade, Inventários realizados |
| **Inventário** | Itens verificados, Sobras encontradas |
| **Movimentação** | Dados do ativo, Locais origem/destino |

##### View de Detalhe (Exemplo):
```python
from django.views.generic import DetailView

class ProdutoDetailView(LoginRequiredMixin, DetailView):
    """Ficha completa com relacionamentos."""
    model = Produto
    template_name = 'produtos/produto_detail.html'
    context_object_name = 'produto'

    def get_queryset(self):
        return (
            Produto.objects.ativos()
            .select_related('marca', 'estilista', 'status')
            .prefetch_related(
                'movimentacoes',
                'inventario_itens',
                'depreciacoes',
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        # Carregar relacionamentos para as tabs
        ctx['movimentacoes'] = obj.movimentacoes.order_by('-data_movimentacao')[:20]
        ctx['depreciacoes'] = obj.depreciacoes.order_by('-ano_referencia', '-mes_referencia')[:12]
        ctx['inventario_itens'] = obj.inventario_itens.select_related('inventario').order_by('-inventario__data_inicio')[:10]
        return ctx

##### Exemplo de Template com Abas (`_detail_relations.html`):
```html
<div x-data="{ tab: 'movimentacoes' }" class="mt-8">
    <div class="border-b border-slate-200 dark:border-slate-700">
        <nav class="-mb-px flex space-x-8" aria-label="Tabs">
            <button @click.prevent="tab = 'movimentacoes'"
                :class="{ 'border-primary-500 text-primary-600 dark:text-primary-400': tab === 'movimentacoes', 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300': tab !== 'movimentacoes' }"
                class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                Movimentações
            </button>
            <button @click.prevent="tab = 'inventarios'"
                :class="{ 'border-primary-500 text-primary-600 dark:text-primary-400': tab === 'inventarios', 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300': tab !== 'inventarios' }"
                class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                Inventários
            </button>
        </nav>
    </div>

    <div x-show="tab === 'movimentacoes'" class="py-4">
        {% include 'patrimonio/partials/_table_movimentacoes.html' with itens=movimentacoes %}
    </div>

    <div x-show="tab === 'inventarios'" class="py-4" style="display: none;">
        {% include 'patrimonio/partials/_table_inventarios.html' with itens=inventario_itens %}
    </div>
</div>
```
```

##### URL Pattern:
```python
# urls.py - SEMPRE incluir a rota de detail
urlpatterns = [
    path('', views.ProdutoListView.as_view(), name='produto-list'),
    path('<int:pk>/', views.ProdutoDetailView.as_view(), name='produto-detail'),  # 👁️
    path('novo/', views.ProdutoCreateView.as_view(), name='produto-create'),
    path('<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto-update'),
    path('<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='produto-delete'),
]
```

##### Ícone na Tabela de Listagem (`_table.html`):
```html
<td class="px-6 py-4 text-right">
    <div class="flex items-center justify-end gap-1">
        <!-- 👁️ Visualizar -->
        <a href="{% url 'modulo:produto-detail' obj.pk %}"
           class="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
           title="Visualizar">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
        </a>
        <!-- ✏️ Editar -->
        <a href="{% url 'modulo:produto-update' obj.pk %}" ...>...</a>
        <!-- 🗑️ Excluir -->
        <button @click="$dispatch('confirm-delete', ...)" ...>...</button>
    </div>
</td>
```

#### Forms (Django Forms)
```python
from django import forms
from .models import Produto


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'referencia', 'descricao', 'marca',
            'estilista', 'status', 'data_entrega_faccao',
            'preco_custo', 'preco_venda',
        ]
        widgets = {
            'data_entrega_faccao': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'descricao': forms.TextInput(
                attrs={'placeholder': 'Descrição do produto'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS a todos os campos
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class',
                'block w-full border-gray-300 dark:border-slate-600 '
                'bg-white dark:bg-slate-800 text-gray-900 dark:text-white '
                'focus:border-primary-500 focus:ring-primary-500 '
                'rounded-md shadow-sm'
            )
```

#### URLs (Namespaced)
```python
# apps/produtos/urls.py
from django.urls import path
from . import views

app_name = 'produtos'

urlpatterns = [
    path('', views.ProdutoListView.as_view(), name='list'),
    path('novo/', views.ProdutoCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='delete'),
]

# config/urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('produtos/', include('apps.produtos.urls')),
    # ... outros módulos
]
```

#### Filters (django-filter)
```python
# apps/produtos/filters.py
import django_filters
from .models import Produto


class ProdutoFilter(django_filters.FilterSet):
    busca = django_filters.CharFilter(
        method='filtrar_busca',
        label='Buscar'
    )
    marca = django_filters.ModelChoiceFilter(
        queryset=lambda: Marca.objects.all()
    )
    status = django_filters.ModelChoiceFilter(
        queryset=lambda: Status.objects.all()
    )
    data_de = django_filters.DateFilter(
        field_name='criado_em',
        lookup_expr='gte',
        label='De'
    )
    data_ate = django_filters.DateFilter(
        field_name='criado_em',
        lookup_expr='lte',
        label='Até'
    )

    class Meta:
        model = Produto
        fields = ['busca', 'marca', 'status']

    def filtrar_busca(self, queryset, name, value):
        return queryset.filter(
            models.Q(referencia__icontains=value) |
            models.Q(descricao__icontains=value)
        )
```

### 4. TEMPLATES DJANGO REUTILIZÁVEIS

#### Layout Base (`templates/base.html`)
```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="csrf-token" content="{{ csrf_token }}">
    <title>{% block title %}{{ APP_NAME }}{% endblock %}</title>

    <!-- Dark Mode Script -->
    <script>
        if (localStorage.getItem('dark-mode') === 'true' ||
            (!('dark-mode' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    </script>

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=figtree:300,400,500,600,700,800&display=swap" rel="stylesheet" />

    <!-- Select2 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />

    <!-- Vite (via django-vite) -->
    {% load django_vite %}
    {% vite_hmr_client %}
    {% vite_asset 'css/app.css' %}
    {% vite_asset 'js/app.js' %}

    {% block extra_css %}{% endblock %}
</head>
<body class="font-sans antialiased text-slate-900 dark:text-slate-100
             bg-slate-50 dark:bg-slate-950 transition-colors duration-300">

    <!-- Loading Overlay -->
    <div id="global-loading-overlay" class="fixed inset-0 bg-slate-900/60
         backdrop-blur-sm flex items-center justify-center z-[100]" style="display: none;">
        <!-- Spinner... -->
    </div>

    <div class="min-h-screen">
        {% include 'includes/_navigation.html' %}

        {% block header %}{% endblock %}

        <!-- Flash Messages -->
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            {% if messages %}
                {% for message in messages %}
                    <div class="glass border-l-4
                        {% if message.tags == 'success' %}border-green-500 bg-green-50/50 dark:bg-green-900/20 text-green-700 dark:text-green-400
                        {% elif message.tags == 'error' %}border-red-500 bg-red-50/50 dark:bg-red-900/20 text-red-700 dark:text-red-400
                        {% elif message.tags == 'warning' %}border-yellow-500 bg-yellow-50/50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400
                        {% else %}border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400
                        {% endif %}
                        p-4 rounded-xl mb-4 relative overflow-hidden" role="alert">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        </div>

        <main>
            {% block content %}{% endblock %}
        </main>
    </div>

    <!-- jQuery & Select2 -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### Card de Estatística (`templates/components/_card_stat.html`)
```html
{# Uso: {% include 'components/_card_stat.html' with label="Total" value=total color="primary" icon="chart" %} #}
<div class="glass dark:glass-dark rounded-2xl p-6 shadow-lg
            hover:shadow-xl transition-all duration-300 group">
    <div class="flex items-center justify-between">
        <div>
            <p class="text-sm font-medium text-slate-500 dark:text-slate-400">
                {{ label }}
            </p>
            <p class="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
                {{ value }}
            </p>
        </div>
        <div class="w-12 h-12 rounded-xl bg-{{ color }}-100 dark:bg-{{ color }}-900/30
                    flex items-center justify-center group-hover:scale-110 transition-transform">
            {% include icon %}
        </div>
    </div>
</div>
```

#### Paginação (`templates/components/_pagination.html`)
```html
{% if page_obj.has_other_pages %}
<nav class="flex items-center justify-between mt-6">
    <div class="text-sm text-slate-500 dark:text-slate-400">
        Mostrando {{ page_obj.start_index }}-{{ page_obj.end_index }}
        de {{ page_obj.paginator.count }} resultados
    </div>
    <div class="flex space-x-1">
        {% if page_obj.has_previous %}
            <a href="?page={{ page_obj.previous_page_number }}&{{ request.GET.urlencode }}"
               class="px-3 py-2 rounded-lg bg-white dark:bg-slate-800
                      hover:bg-primary-50 dark:hover:bg-primary-900/20
                      text-sm transition-colors">
                ← Anterior
            </a>
        {% endif %}

        {% for num in page_obj.paginator.page_range %}
            {% if page_obj.number == num %}
                <span class="px-3 py-2 rounded-lg bg-primary-600 text-white text-sm">
                    {{ num }}
                </span>
            {% else %}
                <a href="?page={{ num }}&{{ request.GET.urlencode }}"
                   class="px-3 py-2 rounded-lg bg-white dark:bg-slate-800
                          hover:bg-primary-50 dark:hover:bg-primary-900/20
                          text-sm transition-colors">
                    {{ num }}
                </a>
            {% endif %}
        {% endfor %}

        {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}&{{ request.GET.urlencode }}"
               class="px-3 py-2 rounded-lg bg-white dark:bg-slate-800
                      hover:bg-primary-50 dark:hover:bg-primary-900/20
                      text-sm transition-colors">
                Próximo →
            </a>
        {% endif %}
    </div>
</nav>
{% endif %}
```

### 5. FUNCIONALIDADES PADRÃO

#### Sistema de Filtros Salvos (UserFilter)
```python
class UserFilter(BaseModel):
    """Filtros salvos por usuário."""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='filtros')
    filter_name = models.CharField(max_length=100)
    filter_type = models.CharField(max_length=50)  # nome do módulo
    filters = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'filter_name', 'filter_type']
```

#### Dashboard com Gráficos
- Cards de estatísticas com cores dinâmicas
- Gráficos Chart.js interativos
- Indicadores de tendência (subiu/desceu)
- Tabela de atividades recentes

#### Kanban Board (opcional)
- Drag & drop entre colunas via Alpine.js + SortableJS
- Cards com informações resumidas
- Filtros por status/responsável

---

## 📝 REQUISITOS FUNCIONAIS

### Módulos Obrigatórios:
1. **Autenticação** (django-allauth + perfis de usuário)
2. **Cadastros Básicos** (CRUDs com soft deletes via BaseModel)
3. **Relacionamentos** (ManyToMany com `through` tables)
4. **Anexos/Arquivos** (upload com validação via `FileField`/`ImageField`)
5. **Auditoria** (django-auditlog em todos os models)
6. **Relatórios** (PDF exportável com WeasyPrint)
7. **Dashboard** (visão geral com métricas via ORM aggregations)

### Funcionalidades UX:
- [ ] Modo escuro/claro persistente
- [ ] Loading states em ações demoradas
- [ ] Toasts/notificações de sucesso/erro (Django messages)
- [ ] Confirmação antes de exclusões (modal Alpine.js)
- [ ] Filtros salvos por usuário
- [ ] Paginação com lazy loading
- [ ] Responsivo (mobile-first)

---

## 🎨 GUIA DE ESTILOS

### Botões
```html
<!-- Primário -->
<button class="btn-primary">Salvar</button>
<!-- CSS: bg-primary-600 hover:bg-primary-700 text-white rounded-lg px-4 py-2 -->

<!-- Fantasma -->
<button class="btn-ghost-primary">
    <svg class="h-4 w-4 mr-1">...</svg>
    Adicionar
</button>
<!-- CSS: text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 -->
```

### Formulários com Django
```html
{% load widget_tweaks %}

<div class="form-group">
    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {{ form.nome.label }} <span class="text-red-500">*</span>
    </label>
    {% render_field form.nome class="block w-full border-gray-300 dark:border-slate-600
           bg-white dark:bg-slate-800 text-gray-900 dark:text-white
           focus:border-primary-500 focus:ring-primary-500
           rounded-md shadow-sm" %}
    {% if form.nome.errors %}
        {% for error in form.nome.errors %}
            <p class="mt-1 text-sm text-red-600">{{ error }}</p>
        {% endfor %}
    {% endif %}
</div>
```

### Tabelas
```html
<div class="glass dark:glass-dark rounded-xl overflow-hidden shadow-lg">
    <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-700">
        <thead class="bg-gray-50 dark:bg-slate-900/50">
            <!-- headers -->
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-slate-700">
            {% for item in itens %}
            <tr class="hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
                <td class="px-6 py-4 text-sm">{{ item.referencia }}</td>
                <td class="px-6 py-4 text-sm">{{ item.descricao }}</td>
                <td class="px-6 py-4 text-sm">{{ item.marca }}</td>
                <td class="px-6 py-4 text-right text-sm space-x-2">
                    <a href="{% url 'produtos:update' item.pk %}" class="btn-ghost-primary">Editar</a>
                    <button @click="confirmDelete({{ item.pk }})" class="btn-ghost-danger">Excluir</button>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="4" class="px-6 py-12 text-center text-slate-400">
                    Nenhum item encontrado.
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% include 'components/_pagination.html' %}
```

---

## 🔧 COMANDOS DE SETUP

```bash
# 1. Criar ambiente virtual e projeto
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install django==5.1

django-admin startproject config .

# 2. Instalar dependências backend
pip install django-allauth
pip install django-auditlog
pip install django-filter
pip install django-widget-tweaks
pip install weasyprint
pip install django-vite
pip install pillow  # para ImageField
pip install gunicorn  # produção

# 3. Criar apps organizadas
mkdir apps
python manage.py startapp core apps/core
python manage.py startapp accounts apps/accounts
python manage.py startapp produtos apps/produtos

# 4. Instalar dependências frontend
npm init -y
npm install -D vite tailwindcss @tailwindcss/forms postcss autoprefixer
npm install alpinejs chart.js jquery select2

# 5. Configurar Tailwind
npx tailwindcss init -p

# 6. Rodar migrations
python manage.py migrate

# 7. Criar superusuário
python manage.py createsuperuser

# 8. Build assets
npm run build

# 9. Iniciar servidor
python manage.py runserver 9000
```

### Configuração `settings/base.py`
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'allauth',
    'allauth.account',
    'auditlog',
    'django_filters',
    'widget_tweaks',
    'django_vite',
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.produtos',
]

# Auditlog
MIDDLEWARE = [
    # ...
    'auditlog.middleware.AuditlogMiddleware',
]

# Allauth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Django Vite
DJANGO_VITE = {
    "default": {
        "dev_mode": DEBUG,
        "dev_server_port": 5173,
    }
}

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

## ✅ CRITÉRIOS DE ACEITAÇÃO

Antes de entregar cada funcionalidade, verificar:

- [ ] Funciona no modo escuro e claro
- [ ] Responsivo (testar em 320px, 768px, 1920px)
- [ ] Mensagens de erro amigáveis (Django messages)
- [ ] Logging de atividades (auditlog registrado)
- [ ] Validação de formulários no frontend e backend
- [ ] Proteção contra CSRF em todos os forms (`{% csrf_token %}`)
- [ ] Ícones consistentes (Lucide/Heroicons)
- [ ] Código sem warnings do Ruff/Flake8
- [ ] Type hints em funções públicas
- [ ] Queries otimizadas (select_related/prefetch_related)

---

## 📚 REFERÊNCIAS

- [Documentação Django 5.x](https://docs.djangoproject.com/en/5.1/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Alpine.js](https://alpinejs.dev/)
- [django-auditlog](https://django-auditlog.readthedocs.io/)
- [django-allauth](https://docs.allauth.org/)
- [django-filter](https://django-filter.readthedocs.io/)
- [django-widget-tweaks](https://github.com/jazzband/django-widget-tweaks)

---

**Crie o sistema seguindo essas diretrizes. Priorize código limpo, consistente e bem documentado com type hints.**

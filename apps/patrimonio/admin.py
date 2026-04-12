"""Django Admin para o módulo Patrimônio."""

from django.contrib import admin

from .models import (
    Ativo,
    AtivoImagem,
    CategoriaContabil,
    CentroCusto,
    DepreciacaoRegistro,
    Imovel,
    Inventario,
    InventarioItem,
    InventarioItemEvidencia,
    InventarioSobra,
    LocalFisico,
    MotivoBaixa,
    Movimentacao,
    Responsavel,
    SituacaoImovel,
    Veiculo,
)


# =============================================================================
# INLINES
# =============================================================================


class DepreciacaoRegistroInline(admin.TabularInline):
    model = DepreciacaoRegistro
    extra = 0
    readonly_fields = [
        'ano_referencia', 'mes_referencia', 'cenario',
        'valor_depreciado_mes', 'depreciacao_acumulada',
        'valor_contabil_atual', 'criado_em',
    ]
    can_delete = False


class MovimentacaoInline(admin.TabularInline):
    model = Movimentacao
    extra = 0
    fk_name = 'ativo'
    readonly_fields = ['criado_em']
    fields = [
        'local_origem', 'local_destino', 'responsavel_anterior',
        'responsavel_novo', 'data_movimentacao', 'status',
    ]


class InventarioItemInline(admin.TabularInline):
    model = InventarioItem
    extra = 0
    raw_id_fields = ['ativo']


class InventarioItemEvidenciaInline(admin.TabularInline):
    model = InventarioItemEvidencia
    extra = 0


class InventarioSobraInline(admin.TabularInline):
    model = InventarioSobra
    extra = 0


class AtivoImagemInline(admin.TabularInline):
    model = AtivoImagem
    extra = 1
    fields = ['imagem', 'descricao', 'tipo', 'principal', 'registrado_por', 'criado_em']
    readonly_fields = ['criado_em']
    raw_id_fields = ['registrado_por']


# =============================================================================
# MODEL ADMINS
# =============================================================================


@admin.register(CategoriaContabil)
class CategoriaContabilAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'taxa_depreciacao_anual', 'vida_util_padrao_meses', 'parent', 'ativo']
    list_filter = ['ativo', 'parent']
    search_fields = ['codigo', 'nome']
    ordering = ['codigo']


@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'departamento', 'unidade', 'ativo']
    list_filter = ['departamento', 'ativo']
    search_fields = ['codigo', 'nome', 'departamento']


@admin.register(LocalFisico)
class LocalFisicoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'edificio', 'andar', 'sala', 'ativo']
    list_filter = ['edificio', 'ativo']
    search_fields = ['codigo', 'edificio', 'sala']


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ['matricula', 'nome', 'cargo', 'email', 'ativo']
    list_filter = ['ativo', 'cargo']
    search_fields = ['nome', 'matricula', 'email']
    raw_id_fields = ['user']


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_tombamento', 'descricao_detalhada', 'categoria',
        'status', 'estado_conservacao', 'valor_aquisicao',
        'depreciavel', 'ativo',
    ]
    list_filter = ['status', 'estado_conservacao', 'depreciavel', 'categoria', 'ativo']
    search_fields = ['numero_tombamento', 'descricao_detalhada', 'nota_fiscal']
    raw_id_fields = ['categoria', 'centro_custo', 'local_fisico', 'responsavel']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [AtivoImagemInline, DepreciacaoRegistroInline, MovimentacaoInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_tombamento', 'descricao_detalhada', 'foto'),
        }),
        ('Classificação', {
            'fields': ('categoria', 'centro_custo', 'local_fisico', 'responsavel'),
        }),
        ('Financeiro', {
            'fields': (
                'data_aquisicao', 'valor_aquisicao', 'valor_residual',
                'vida_util_meses', 'depreciavel',
            ),
        }),
        ('Estado', {
            'fields': ('status', 'estado_conservacao'),
        }),
        ('Aquisição', {
            'fields': ('nota_fiscal', 'fornecedor'),
            'classes': ('collapse',),
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',),
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em', 'ativo'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Tombamento readonly após criação."""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.append('numero_tombamento')
        return readonly


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = [
        'ativo', 'local_origem', 'local_destino',
        'data_movimentacao', 'status',
    ]
    list_filter = ['status', 'data_movimentacao']
    search_fields = ['ativo__numero_tombamento', 'motivo']
    raw_id_fields = [
        'ativo', 'local_origem', 'local_destino',
        'responsavel_anterior', 'responsavel_novo',
    ]
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(DepreciacaoRegistro)
class DepreciacaoRegistroAdmin(admin.ModelAdmin):
    list_display = [
        'ativo', 'mes_referencia', 'ano_referencia', 'cenario',
        'valor_depreciado_mes', 'depreciacao_acumulada',
        'valor_contabil_atual',
    ]
    list_filter = ['cenario', 'ano_referencia', 'mes_referencia']
    search_fields = ['ativo__numero_tombamento']
    raw_id_fields = ['ativo']
    readonly_fields = ['criado_em']


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'data_inicio', 'data_fim', 'responsavel', 'status']
    list_filter = ['status']
    search_fields = ['codigo']
    inlines = [InventarioItemInline, InventarioSobraInline]
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(InventarioItem)
class InventarioItemAdmin(admin.ModelAdmin):
    list_display = ['inventario', 'ativo', 'presenca', 'estado_conservacao_encontrado']
    list_filter = ['presenca', 'inventario']
    search_fields = ['ativo__numero_tombamento']
    raw_id_fields = ['ativo', 'inventario']
    inlines = [InventarioItemEvidenciaInline]


@admin.register(InventarioSobra)
class InventarioSobraAdmin(admin.ModelAdmin):
    list_display = ['inventario', 'descricao_item', 'local_encontrado']
    list_filter = ['inventario']
    search_fields = ['descricao_item']


@admin.register(MotivoBaixa)
class MotivoBaixaAdmin(admin.ModelAdmin):
    list_display = ['ativo', 'tipo', 'data_baixa', 'valor_contabil_baixa', 'autorizado_por']
    list_filter = ['tipo', 'data_baixa']
    search_fields = ['ativo__numero_tombamento', 'justificativa']
    raw_id_fields = ['ativo']
    readonly_fields = ['criado_em']


# =============================================================================
# IMÓVEL
# =============================================================================


class SituacaoImovelInline(admin.TabularInline):
    model = SituacaoImovel
    extra = 0
    fields = ['situacao', 'data_inicio', 'data_fim', 'observacoes', 'registrado_por']
    readonly_fields = ['criado_em']


@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    list_display = [
        'numero_tombamento', 'tipo_imovel', 'descricao_detalhada',
        'area_total_m2', 'status', 'valor_aquisicao', 'ativo',
    ]
    list_filter = ['tipo_imovel', 'status', 'estado_conservacao', 'ativo']
    search_fields = ['numero_tombamento', 'descricao_detalhada', 'endereco_completo', 'matricula_registro']
    raw_id_fields = ['categoria', 'centro_custo', 'local_fisico', 'responsavel']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [SituacaoImovelInline]


@admin.register(SituacaoImovel)
class SituacaoImovelAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'situacao', 'data_inicio', 'data_fim', 'registrado_por']
    list_filter = ['situacao']
    search_fields = ['imovel__numero_tombamento', 'observacoes']
    raw_id_fields = ['imovel']


# =============================================================================
# VEÍCULO
# =============================================================================


@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = [
        'placa', 'marca_modelo', 'ano_fabricacao', 'ano_modelo',
        'combustivel', 'status', 'valor_aquisicao', 'ativo',
    ]
    list_filter = ['combustivel', 'status', 'estado_conservacao', 'ativo']
    search_fields = ['placa', 'marca_modelo', 'renavam', 'chassi', 'numero_tombamento']
    raw_id_fields = ['categoria', 'centro_custo', 'local_fisico', 'responsavel']
    readonly_fields = ['criado_em', 'atualizado_em']


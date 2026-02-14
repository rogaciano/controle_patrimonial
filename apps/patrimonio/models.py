"""
Models do módulo Patrimônio.

Entidades: CategoriaContabil, CentroCusto, LocalFisico, Responsavel,
Ativo, Movimentacao, DepreciacaoRegistro, Inventario, InventarioItem,
InventarioItemEvidencia, InventarioSobra, MotivoBaixa.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from auditlog.registry import auditlog

from apps.core.models import BaseModel
from apps.core.validators import validar_telefone


# =============================================================================
# TABELAS AUXILIARES
# =============================================================================


class CategoriaContabil(BaseModel):
    """Classificação hierárquica dos ativos com taxas de depreciação padrão."""

    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategorias',
        verbose_name='Categoria Pai',
    )
    nome = models.CharField(
        max_length=150,
        verbose_name='Nome',
    )
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código Contábil',
    )
    taxa_depreciacao_anual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Taxa Depreciação Anual (%)',
        help_text='Percentual ao ano. Ex: 20.00 = 20%',
    )
    vida_util_padrao_meses = models.PositiveIntegerField(
        verbose_name='Vida Útil Padrão (meses)',
        help_text='Vida útil padrão em meses. Ex: 60',
    )
    descricao = models.TextField(
        blank=True,
        default='',
        verbose_name='Descrição',
    )

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Categoria Contábil'
        verbose_name_plural = 'Categorias Contábeis'

    def __str__(self) -> str:
        return f'{self.codigo} - {self.nome}'

    def get_absolute_url(self) -> str:
        return reverse('patrimonio:categoria-detail', kwargs={'pk': self.pk})


class CentroCusto(BaseModel):
    """Estrutura organizacional (departamento/unidade)."""

    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
    )
    nome = models.CharField(
        max_length=150,
        verbose_name='Nome',
    )
    departamento = models.CharField(
        max_length=100,
        verbose_name='Departamento',
    )
    unidade = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Unidade',
    )

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Centro de Custo'
        verbose_name_plural = 'Centros de Custo'

    def __str__(self) -> str:
        return f'{self.codigo} - {self.nome}'


class LocalFisico(BaseModel):
    """Localização física detalhada (edifício, andar, sala)."""

    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
    )
    edificio = models.CharField(
        max_length=100,
        verbose_name='Edifício',
    )
    andar = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Andar',
    )
    sala = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Sala',
    )
    descricao = models.TextField(
        blank=True,
        default='',
        verbose_name='Descrição',
    )

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Local Físico'
        verbose_name_plural = 'Locais Físicos'

    def __str__(self) -> str:
        parts = [self.edificio]
        if self.andar:
            parts.append(self.andar)
        if self.sala:
            parts.append(self.sala)
        return ' / '.join(parts)


class Responsavel(BaseModel):
    """Colaborador que detém a guarda de bens patrimoniais."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsavel_patrimonial',
        verbose_name='Usuário do Sistema',
    )
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome Completo',
    )
    matricula = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Matrícula',
    )
    cargo = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Cargo',
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name='E-mail',
    )
    telefone = models.CharField(
        max_length=11,
        blank=True,
        default='',
        validators=[validar_telefone],
        verbose_name='Telefone',
    )

    class Meta:
        ordering = ['nome']
        verbose_name = 'Responsável'
        verbose_name_plural = 'Responsáveis'

    def __str__(self) -> str:
        return f'{self.matricula} - {self.nome}'


# =============================================================================
# ATIVO PATRIMONIAL (ENTIDADE CENTRAL)
# =============================================================================


class Ativo(BaseModel):
    """Bem patrimonial — entidade central do sistema."""

    class EstadoConservacao(models.TextChoices):
        NOVO = 'NOVO', 'Novo'
        BOM = 'BOM', 'Bom'
        REGULAR = 'REGULAR', 'Regular'
        RUIM = 'RUIM', 'Ruim'
        INSERVIVEL = 'INSERVIVEL', 'Inservível/Sucata'

    class Status(models.TextChoices):
        ATIVO = 'ATIVO', 'Ativo'
        EM_MANUTENCAO = 'EM_MANUTENCAO', 'Em Manutenção'
        EM_PROCESSO_BAIXA = 'EM_PROCESSO_BAIXA', 'Em Processo de Baixa'
        BAIXADO = 'BAIXADO', 'Baixado'

    numero_tombamento = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Nº Tombamento',
        help_text='Número único e imutável da plaqueta/etiqueta.',
    )
    descricao_detalhada = models.TextField(
        verbose_name='Descrição Detalhada',
    )
    categoria = models.ForeignKey(
        CategoriaContabil,
        on_delete=models.PROTECT,
        related_name='ativos',
        verbose_name='Categoria Contábil',
    )
    centro_custo = models.ForeignKey(
        CentroCusto,
        on_delete=models.PROTECT,
        related_name='ativos',
        verbose_name='Centro de Custo',
    )
    local_fisico = models.ForeignKey(
        LocalFisico,
        on_delete=models.PROTECT,
        related_name='ativos',
        verbose_name='Local Físico',
    )
    responsavel = models.ForeignKey(
        Responsavel,
        on_delete=models.PROTECT,
        related_name='ativos',
        verbose_name='Responsável',
    )
    data_aquisicao = models.DateField(
        verbose_name='Data de Aquisição',
    )
    valor_aquisicao = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor de Aquisição (R$)',
    )
    valor_residual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Valor Residual (R$)',
    )
    vida_util_meses = models.PositiveIntegerField(
        verbose_name='Vida Útil (meses)',
    )
    estado_conservacao = models.CharField(
        max_length=15,
        choices=EstadoConservacao.choices,
        default=EstadoConservacao.NOVO,
        verbose_name='Estado de Conservação',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
        verbose_name='Status',
    )
    depreciavel = models.BooleanField(
        default=True,
        verbose_name='Depreciável',
        help_text='Desmarque para terrenos ou itens sem depreciação.',
    )
    nota_fiscal = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Nota Fiscal',
    )
    fornecedor = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Fornecedor',
    )
    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name='Observações',
    )
    foto = models.ImageField(
        upload_to='ativos/',
        blank=True,
        null=True,
        verbose_name='Foto',
    )

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Ativo'
        verbose_name_plural = 'Ativos'

    def __str__(self) -> str:
        return f'{self.numero_tombamento} - {self.descricao_detalhada[:50]}'

    def get_absolute_url(self) -> str:
        return reverse('patrimonio:ativo-detail', kwargs={'pk': self.pk})

    def clean(self) -> None:
        """Impede alteração do número de tombamento após criação."""
        super().clean()
        if self.pk:
            try:
                original = Ativo.objects.get(pk=self.pk)
                if original.numero_tombamento != self.numero_tombamento:
                    raise ValidationError(
                        {'numero_tombamento': 'O número de tombamento não pode ser alterado.'}
                    )
            except Ativo.DoesNotExist:
                pass

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    # --- Properties Calculadas ---

    @property
    def valor_contabil_atual(self) -> Decimal:
        """Net Book Value = Aquisição - Depreciação Acumulada."""
        ultimo = self.depreciacoes.filter(
            cenario='FISCAL'
        ).order_by('-ano_referencia', '-mes_referencia').first()
        return ultimo.valor_contabil_atual if ultimo else self.valor_aquisicao

    @property
    def depreciacao_acumulada_total(self) -> Decimal:
        """Soma total depreciada até o momento (cenário fiscal)."""
        ultimo = self.depreciacoes.filter(
            cenario='FISCAL'
        ).order_by('-ano_referencia', '-mes_referencia').first()
        return ultimo.depreciacao_acumulada if ultimo else Decimal('0.00')

    @property
    def percentual_depreciado(self) -> Decimal:
        """Percentual já depreciado."""
        if self.valor_aquisicao == 0:
            return Decimal('0.00')
        return (
            self.depreciacao_acumulada_total / self.valor_aquisicao * 100
        ).quantize(Decimal('0.01'))

    @property
    def meses_restantes_vida_util(self) -> int:
        """Meses faltantes para depreciação total."""
        meses_depr = self.depreciacoes.filter(cenario='FISCAL').count()
        return max(0, self.vida_util_meses - meses_depr)

    # --- QuerySet Customizado ---

    class AtivoQuerySet(models.QuerySet):
        def ativos_operacionais(self):
            return self.filter(ativo=True).exclude(status='BAIXADO')

        def depreciaveis(self):
            return self.filter(depreciavel=True, ativo=True).exclude(status='BAIXADO')

        def por_categoria(self, categoria_id: int):
            return self.filter(categoria_id=categoria_id)

        def por_local(self, local_id: int):
            return self.filter(local_fisico_id=local_id)

        def por_responsavel(self, responsavel_id: int):
            return self.filter(responsavel_id=responsavel_id)

    objects = AtivoQuerySet.as_manager()


# =============================================================================
# MOVIMENTAÇÃO (HISTÓRICO DE TRANSFERÊNCIAS)
# =============================================================================


class Movimentacao(BaseModel):
    """Log de transferências de bens patrimoniais."""

    class StatusMovimentacao(models.TextChoices):
        SOLICITADA = 'SOLICITADA', 'Solicitada'
        APROVADA = 'APROVADA', 'Aprovada'
        CONCLUIDA = 'CONCLUIDA', 'Concluída'
        CANCELADA = 'CANCELADA', 'Cancelada'

    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        verbose_name='Ativo',
    )
    local_origem = models.ForeignKey(
        LocalFisico,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Local de Origem',
    )
    local_destino = models.ForeignKey(
        LocalFisico,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Local de Destino',
    )
    responsavel_anterior = models.ForeignKey(
        Responsavel,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Responsável Anterior',
    )
    responsavel_novo = models.ForeignKey(
        Responsavel,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Novo Responsável',
    )
    centro_custo_origem = models.ForeignKey(
        CentroCusto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Centro de Custo Origem',
    )
    centro_custo_destino = models.ForeignKey(
        CentroCusto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Centro de Custo Destino',
    )
    data_movimentacao = models.DateField(
        verbose_name='Data da Movimentação',
    )
    motivo = models.TextField(
        verbose_name='Motivo',
    )
    status = models.CharField(
        max_length=15,
        choices=StatusMovimentacao.choices,
        default=StatusMovimentacao.SOLICITADA,
        verbose_name='Status',
    )
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_aprovadas',
        verbose_name='Aprovado por',
    )

    class Meta:
        ordering = ['-data_movimentacao']
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'

    def __str__(self) -> str:
        return (
            f'Mov. {self.ativo.numero_tombamento}: '
            f'{self.local_origem} → {self.local_destino}'
        )


# =============================================================================
# DEPRECIAÇÃO
# =============================================================================


class DepreciacaoRegistro(models.Model):
    """Registro mensal de depreciação de um ativo."""

    class Cenario(models.TextChoices):
        FISCAL = 'FISCAL', 'Fiscal'
        SOCIETARIO = 'SOCIETARIO', 'Societário/Gerencial'

    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.CASCADE,
        related_name='depreciacoes',
        verbose_name='Ativo',
    )
    ano_referencia = models.PositiveIntegerField(
        verbose_name='Ano',
    )
    mes_referencia = models.PositiveSmallIntegerField(
        verbose_name='Mês',
    )
    cenario = models.CharField(
        max_length=15,
        choices=Cenario.choices,
        default=Cenario.FISCAL,
        verbose_name='Cenário',
    )
    valor_depreciado_mes = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Depreciação do Mês (R$)',
    )
    depreciacao_acumulada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Depreciação Acumulada (R$)',
    )
    valor_contabil_atual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor Contábil Atual (R$)',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ano_referencia', '-mes_referencia']
        unique_together = ['ativo', 'ano_referencia', 'mes_referencia', 'cenario']
        verbose_name = 'Registro de Depreciação'
        verbose_name_plural = 'Registros de Depreciação'

    def __str__(self) -> str:
        return (
            f'{self.ativo.numero_tombamento} - '
            f'{self.mes_referencia:02d}/{self.ano_referencia} '
            f'({self.cenario})'
        )


# =============================================================================
# INVENTÁRIO
# =============================================================================


class Inventario(BaseModel):
    """Cabeçalho de um inventário patrimonial."""

    class StatusInventario(models.TextChoices):
        ABERTO = 'ABERTO', 'Aberto'
        EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'
        CANCELADO = 'CANCELADO', 'Cancelado'

    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
    )
    data_inicio = models.DateField(
        verbose_name='Data de Início',
    )
    data_fim = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Encerramento',
    )
    responsavel = models.ForeignKey(
        Responsavel,
        on_delete=models.PROTECT,
        related_name='inventarios',
        verbose_name='Coordenador',
    )
    status = models.CharField(
        max_length=15,
        choices=StatusInventario.choices,
        default=StatusInventario.ABERTO,
        verbose_name='Status',
    )
    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name='Observações',
    )

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = 'Inventário'
        verbose_name_plural = 'Inventários'

    def __str__(self) -> str:
        return f'{self.codigo} ({self.get_status_display()})'

    def get_absolute_url(self) -> str:
        return reverse('patrimonio:inventario-detail', kwargs={'pk': self.pk})


class InventarioItem(models.Model):
    """Item de conferência de um inventário."""

    class Presenca(models.TextChoices):
        LOCALIZADO = 'LOCALIZADO', 'Localizado'
        NAO_LOCALIZADO = 'NAO_LOCALIZADO', 'Não Localizado'

    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Inventário',
    )
    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.PROTECT,
        related_name='itens_inventario',
        verbose_name='Ativo',
    )
    presenca = models.CharField(
        max_length=20,
        choices=Presenca.choices,
        default=Presenca.NAO_LOCALIZADO,
        verbose_name='Presença',
    )
    estado_conservacao_encontrado = models.CharField(
        max_length=15,
        choices=Ativo.EstadoConservacao.choices,
        blank=True,
        default='',
        verbose_name='Estado Encontrado',
    )
    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name='Observações',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ativo__numero_tombamento']
        unique_together = ['inventario', 'ativo']
        verbose_name = 'Item de Inventário'
        verbose_name_plural = 'Itens de Inventário'

    def __str__(self) -> str:
        return (
            f'{self.ativo.numero_tombamento} - '
            f'{self.get_presenca_display()}'
        )


class InventarioItemEvidencia(models.Model):
    """Evidência (foto/documento) de item de inventário."""

    item = models.ForeignKey(
        InventarioItem,
        on_delete=models.CASCADE,
        related_name='evidencias',
        verbose_name='Item',
    )
    arquivo = models.FileField(
        upload_to='inventarios/evidencias/',
        verbose_name='Arquivo',
    )
    descricao = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Descrição',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidência de Inventário'
        verbose_name_plural = 'Evidências de Inventário'

    def __str__(self) -> str:
        return f'Evidência: {self.item} - {self.descricao or self.arquivo.name}'


class InventarioSobra(models.Model):
    """Bens encontrados sem etiqueta durante o inventário (sobras)."""

    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name='sobras',
        verbose_name='Inventário',
    )
    descricao_item = models.TextField(
        verbose_name='Descrição do Item',
    )
    local_encontrado = models.ForeignKey(
        LocalFisico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Local Encontrado',
    )
    foto = models.ImageField(
        upload_to='inventarios/sobras/',
        blank=True,
        null=True,
        verbose_name='Foto',
    )
    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name='Observações',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sobra de Inventário'
        verbose_name_plural = 'Sobras de Inventário'

    def __str__(self) -> str:
        return f'Sobra: {self.descricao_item[:50]}'


# =============================================================================
# BAIXA PATRIMONIAL
# =============================================================================


class MotivoBaixa(models.Model):
    """Registro de baixa patrimonial de um ativo."""

    class TipoBaixa(models.TextChoices):
        OBSOLESCENCIA = 'OBSOLESCENCIA', 'Obsolescência'
        FURTO = 'FURTO', 'Furto/Roubo'
        VENDA = 'VENDA', 'Venda'
        DOACAO = 'DOACAO', 'Doação'
        SINISTRO = 'SINISTRO', 'Sinistro'
        OUTRO = 'OUTRO', 'Outro'

    ativo = models.OneToOneField(
        Ativo,
        on_delete=models.CASCADE,
        related_name='baixa',
        verbose_name='Ativo',
    )
    tipo = models.CharField(
        max_length=15,
        choices=TipoBaixa.choices,
        verbose_name='Tipo de Baixa',
    )
    data_baixa = models.DateField(
        verbose_name='Data da Baixa',
    )
    justificativa = models.TextField(
        verbose_name='Justificativa',
    )
    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='baixas_autorizadas',
        verbose_name='Autorizado por',
    )
    valor_contabil_baixa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor Contábil na Baixa (R$)',
    )
    documento_comprovante = models.FileField(
        upload_to='baixas/',
        blank=True,
        null=True,
        verbose_name='Documento Comprovante',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Motivo de Baixa'
        verbose_name_plural = 'Motivos de Baixa'

    def __str__(self) -> str:
        return (
            f'Baixa: {self.ativo.numero_tombamento} - '
            f'{self.get_tipo_display()}'
        )


# =============================================================================
# REGISTRO NO AUDITLOG
# =============================================================================

auditlog.register(CategoriaContabil)
auditlog.register(CentroCusto)
auditlog.register(LocalFisico)
auditlog.register(Responsavel)
auditlog.register(Ativo)
auditlog.register(Movimentacao)
auditlog.register(Inventario)
auditlog.register(MotivoBaixa)

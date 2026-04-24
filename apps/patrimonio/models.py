"""
Models do módulo Patrimônio.

Entidades: CategoriaContabil, CentroCusto, LocalFisico, Responsavel,
Ativo, AtivoImagem, Movimentacao, DepreciacaoRegistro, Inventario,
InventarioItem, InventarioItemEvidencia, InventarioSobra, MotivoBaixa.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import IntegerField, Max
from django.db.models.functions import Cast, Substr
from django.urls import reverse
from django.utils import timezone

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
    
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.PROTECT,
        default=1,
        verbose_name='Empresa',
        related_name='centros_custo',
    )
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

    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.PROTECT,
        default=1,
        verbose_name='Empresa',
        related_name='locais_fisicos',
    )
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

    @property
    def nome(self):
        """Retorna a representação em string como nome."""
        return str(self)


class Responsavel(BaseModel):
    """Colaborador que detém a guarda de bens patrimoniais."""

    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.PROTECT,
        default=1,
        verbose_name='Empresa',
        related_name='responsaveis',
    )
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

    @property
    def codigo(self):
        """Retorna a matrícula como código."""
        return self.matricula


# =============================================================================
# ATIVO PATRIMONIAL (ENTIDADE CENTRAL)
# =============================================================================


class Ativo(BaseModel):
    """Bem patrimonial — entidade central do sistema."""

    _TOMBAMENTO_REGEX = r'^[A-Za-z0-9]{3}-\d{2}-\d{6}$'

    class TipoAtivo(models.TextChoices):
        EQUIPAMENTO = 'EQUIPAMENTO', 'Móvel/Equipamento'
        IMOVEL = 'IMOVEL', 'Imóvel'
        VEICULO = 'VEICULO', 'Veículo'

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

    tipo = models.CharField(
        max_length=15,
        choices=TipoAtivo.choices,
        default=TipoAtivo.EQUIPAMENTO,
        verbose_name='Tipo de Ativo',
        db_index=True,
    )
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.PROTECT,
        default=1,
        verbose_name='Empresa',
        related_name='ativos',
    )
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
        permissions = [
            ('can_change_asset_status', 'Pode alterar status de ativo'),
            ('can_set_asset_maintenance', 'Pode colocar ativo em manutenção'),
            ('can_return_asset_to_active', 'Pode retornar ativo para status ativo'),
            ('can_process_asset_disposal', 'Pode iniciar/processar baixa patrimonial'),
        ]

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

    @classmethod
    def _proximo_sequencial_tombamento(cls) -> int:
        max_seq = (
            cls.objects.filter(numero_tombamento__regex=cls._TOMBAMENTO_REGEX)
            .annotate(
                _seq=Cast(
                    Substr('numero_tombamento', 8, 6),
                    output_field=IntegerField(),
                )
            )
            .aggregate(Max('_seq'))
            .get('_seq__max')
        )
        return (max_seq or 0) + 1

    def _gerar_numero_tombamento(self) -> str:
        codigo = (self.categoria.codigo or '').strip().upper()
        codigo = ''.join(ch for ch in codigo if ch.isalnum())
        if len(codigo) >= 3:
            prefixo = codigo[:3]
        else:
            prefixo = codigo.rjust(3, '0')

        ano = timezone.localdate().year % 100
        sequencial = self._proximo_sequencial_tombamento()
        return f'{prefixo}-{ano:02d}-{sequencial:06d}'

    def save(self, *args, **kwargs) -> None:
        if not self.pk and not (self.numero_tombamento or '').strip():
            tentativas = 5
            last_error = None
            for _ in range(tentativas):
                with transaction.atomic():
                    self.numero_tombamento = self._gerar_numero_tombamento()
                    self.full_clean()
                    try:
                        super().save(*args, **kwargs)
                        return
                    except IntegrityError as e:
                        last_error = e
                        self.numero_tombamento = ''
                        continue
            raise last_error

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
# HISTÓRICO DE MUDANÇA DE STATUS
# =============================================================================


class AtivoStatusHistorico(models.Model):
    """Trilha de mudanças de status do ativo com motivo e justificativa."""

    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.CASCADE,
        related_name='historico_status',
        verbose_name='Ativo',
    )
    status_anterior = models.CharField(
        max_length=20,
        choices=Ativo.Status.choices,
        verbose_name='Status Anterior',
    )
    status_novo = models.CharField(
        max_length=20,
        choices=Ativo.Status.choices,
        verbose_name='Status Novo',
    )
    motivo = models.CharField(max_length=40, verbose_name='Motivo')
    justificativa = models.TextField(
        blank=True,
        default='',
        verbose_name='Justificativa detalhada',
    )
    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alteracoes_status_ativo',
        verbose_name='Alterado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico de Status do Ativo'
        verbose_name_plural = 'Histórico de Status dos Ativos'

    def __str__(self) -> str:
        return (
            f'{self.ativo.numero_tombamento}: '
            f'{self.status_anterior} -> {self.status_novo} ({self.motivo})'
        )


# =============================================================================
# GALERIA DE IMAGENS DO ATIVO
# =============================================================================


class AtivoImagem(models.Model):
    """Imagem da galeria de um ativo patrimonial."""

    class TipoImagem(models.TextChoices):
        AQUISICAO = 'AQUISICAO', 'Aquisição'
        INVENTARIO = 'INVENTARIO', 'Inventário'
        MANUTENCAO = 'MANUTENCAO', 'Manutenção'
        DANO = 'DANO', 'Dano'
        OUTRO = 'OUTRO', 'Outro'

    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.CASCADE,
        related_name='imagens',
        verbose_name='Ativo',
    )
    imagem = models.ImageField(
        upload_to='ativos/galeria/',
        verbose_name='Imagem',
    )
    descricao = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Descrição',
        help_text='Ex: Vista frontal, Número de série, Dano lateral',
    )
    tipo = models.CharField(
        max_length=15,
        choices=TipoImagem.choices,
        default=TipoImagem.OUTRO,
        verbose_name='Tipo',
    )
    principal = models.BooleanField(
        default=False,
        verbose_name='Foto Principal',
        help_text='Marque para exibir esta imagem em destaque na ficha do ativo.',
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagens_patrimonio',
        verbose_name='Registrado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-principal', '-criado_em']
        verbose_name = 'Imagem do Ativo'
        verbose_name_plural = 'Imagens do Ativo'

    def __str__(self) -> str:
        label = self.descricao or self.get_tipo_display()
        star = ' ⭐' if self.principal else ''
        return f'{self.ativo.numero_tombamento} - {label}{star}'

    def save(self, *args, **kwargs) -> None:
        # Auto-unmark: garante que apenas UMA imagem seja principal por ativo
        if self.principal:
            AtivoImagem.objects.filter(
                ativo=self.ativo, principal=True,
            ).exclude(pk=self.pk).update(principal=False)
        super().save(*args, **kwargs)


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
        blank=True,
        verbose_name='Código',
        help_text='Deixe em branco para gerar automaticamente (DDMMYYHHMM)',
    )
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.PROTECT,
        default=1,
        related_name='inventarios',
        verbose_name='Empresa',
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

    def save(self, *args, **kwargs):
        if not self.codigo:
            from django.utils import timezone
            # DDMMYYHHMM
            self.codigo = timezone.localtime().strftime('%d%m%y%H%M')
        super().save(*args, **kwargs)


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
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inventario_itens_confirmados',
        verbose_name='Confirmado por',
    )
    confirmado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Confirmado em',
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

    class Tipo(models.TextChoices):
        GERAL = 'GERAL', 'Geral'
        AVARIA = 'AVARIA', 'Avaria'

    item = models.ForeignKey(
        InventarioItem,
        on_delete=models.CASCADE,
        related_name='evidencias',
        verbose_name='Item',
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.GERAL,
        verbose_name='Tipo',
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
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inventario_evidencias_criadas',
        verbose_name='Criado por',
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
# IMÓVEL (HERANÇA MULTI-TABELA)
# =============================================================================


class Imovel(Ativo):
    """Imóvel patrimonial — herda todos os campos de Ativo."""

    class TipoImovel(models.TextChoices):
        TERRENO = 'TERRENO', 'Terreno'
        PREDIO = 'PREDIO', 'Prédio'
        SALA = 'SALA', 'Sala Comercial'
        GALPAO = 'GALPAO', 'Galpão'
        APARTAMENTO = 'APARTAMENTO', 'Apartamento'
        CASA = 'CASA', 'Casa'
        LOTE = 'LOTE', 'Lote'
        OUTRO = 'OUTRO', 'Outro'

    tipo_imovel = models.CharField(
        max_length=15,
        choices=TipoImovel.choices,
        verbose_name='Tipo de Imóvel',
    )
    matricula_registro = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Matrícula/Registro',
        help_text='Número da matrícula no cartório de registro de imóveis.',
    )
    cartorio = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name='Cartório',
    )
    area_total_m2 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Área Total (m²)',
    )
    endereco_completo = models.TextField(
        blank=True,
        default='',
        verbose_name='Endereço Completo',
    )
    numero_iptu = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name='Nº Inscrição IPTU',
    )

    class Meta:
        verbose_name = 'Imóvel'
        verbose_name_plural = 'Imóveis'

    def __str__(self) -> str:
        return f'{self.numero_tombamento} - {self.get_tipo_imovel_display()} - {self.descricao_detalhada[:50]}'

    def get_absolute_url(self) -> str:
        return reverse('patrimonio:imovel-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs) -> None:
        self.tipo = Ativo.TipoAtivo.IMOVEL
        super().save(*args, **kwargs)

    @property
    def situacao_atual(self):
        """Retorna a situação mais recente do imóvel."""
        return self.situacoes.filter(ativo=True).order_by('-data_inicio').first()


class SituacaoImovel(BaseModel):
    """Acompanhamento de situação/ocorrência de um imóvel."""

    class Situacao(models.TextChoices):
        DISPONIVEL = 'DISPONIVEL', 'Disponível'
        ALUGADO = 'ALUGADO', 'Alugado'
        CEDIDO = 'CEDIDO', 'Cedido'
        EM_REFORMA = 'EM_REFORMA', 'Em Reforma'
        FECHADO = 'FECHADO', 'Fechado'
        EM_USO_PROPRIO = 'EM_USO_PROPRIO', 'Em Uso Próprio'
        OUTRO = 'OUTRO', 'Outro'

    imovel = models.ForeignKey(
        Imovel,
        on_delete=models.CASCADE,
        related_name='situacoes',
        verbose_name='Imóvel',
    )
    situacao = models.CharField(
        max_length=15,
        choices=Situacao.choices,
        verbose_name='Situação',
    )
    data_inicio = models.DateField(
        verbose_name='Data de Início',
    )
    data_fim = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Término',
    )
    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name='Observações',
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='situacoes_imovel_registradas',
        verbose_name='Registrado por',
    )

    class Meta:
        ordering = ['-data_inicio', '-criado_em']
        verbose_name = 'Situação do Imóvel'
        verbose_name_plural = 'Situações dos Imóveis'

    def __str__(self) -> str:
        return f'{self.imovel.numero_tombamento} - {self.get_situacao_display()} ({self.data_inicio})'


# =============================================================================
# VEÍCULO (HERANÇA MULTI-TABELA)
# =============================================================================


class Veiculo(Ativo):
    """Veículo patrimonial — herda todos os campos de Ativo."""

    class TipoCombustivel(models.TextChoices):
        GASOLINA = 'GASOLINA', 'Gasolina'
        ETANOL = 'ETANOL', 'Etanol'
        FLEX = 'FLEX', 'Flex'
        DIESEL = 'DIESEL', 'Diesel'
        ELETRICO = 'ELETRICO', 'Elétrico'
        HIBRIDO = 'HIBRIDO', 'Híbrido'

    placa = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Placa',
        help_text='Formato Mercosul ou antigo (ex: ABC1D23 ou ABC-1234)',
    )
    renavam = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        default='',
        verbose_name='RENAVAM',
    )
    chassi = models.CharField(
        max_length=25,
        blank=True,
        default='',
        verbose_name='Chassi',
    )
    marca_modelo = models.CharField(
        max_length=100,
        verbose_name='Marca/Modelo',
        help_text='Ex: Fiat Uno, Toyota Hilux',
    )
    ano_fabricacao = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Ano de Fabricação',
    )
    ano_modelo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Ano do Modelo',
    )
    cor = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name='Cor',
    )
    combustivel = models.CharField(
        max_length=10,
        choices=TipoCombustivel.choices,
        default=TipoCombustivel.FLEX,
        verbose_name='Combustível',
    )

    class Meta:
        verbose_name = 'Veículo'
        verbose_name_plural = 'Veículos'

    def __str__(self) -> str:
        return f'{self.placa} - {self.marca_modelo}'

    def get_absolute_url(self) -> str:
        return reverse('patrimonio:veiculo-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs) -> None:
        self.tipo = Ativo.TipoAtivo.VEICULO
        self.placa = self.placa.upper().strip()
        super().save(*args, **kwargs)


# =============================================================================
# REGISTRO NO AUDITLOG
# =============================================================================

auditlog.register(CategoriaContabil)
auditlog.register(CentroCusto)
auditlog.register(LocalFisico)
auditlog.register(Responsavel)
auditlog.register(Ativo)
auditlog.register(AtivoStatusHistorico)
auditlog.register(Movimentacao)
auditlog.register(Inventario)
auditlog.register(MotivoBaixa)
auditlog.register(AtivoImagem)
auditlog.register(Imovel)
auditlog.register(SituacaoImovel)
auditlog.register(Veiculo)

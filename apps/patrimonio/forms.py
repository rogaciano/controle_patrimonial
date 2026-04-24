"""Django Forms para o módulo Patrimônio."""

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Ativo,
    AtivoImagem,
    CategoriaContabil,
    CentroCusto,
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


class _BaseForm(forms.ModelForm):
    """Mixin para aplicar classes CSS padrão a todos os campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault(
                    'class',
                    'block w-full border-gray-300 dark:border-slate-600 '
                    'bg-white dark:bg-slate-800 text-gray-900 dark:text-white '
                    'focus:border-primary-500 focus:ring-primary-500 '
                    'rounded-md shadow-sm',
                )
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault(
                    'class',
                    'rounded border-gray-300 dark:border-slate-600 '
                    'text-primary-600 focus:ring-primary-500',
                )
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault(
                    'class',
                    'block w-full border-gray-300 dark:border-slate-600 '
                    'bg-white dark:bg-slate-800 text-gray-900 dark:text-white '
                    'focus:border-primary-500 focus:ring-primary-500 '
                    'rounded-md shadow-sm',
                )
                widget.attrs.setdefault('rows', 3)
            else:
                widget.attrs.setdefault(
                    'class',
                    'block w-full border-gray-300 dark:border-slate-600 '
                    'bg-white dark:bg-slate-800 text-gray-900 dark:text-white '
                    'focus:border-primary-500 focus:ring-primary-500 '
                    'rounded-md shadow-sm',
                )


# =============================================================================
# CADASTROS AUXILIARES
# =============================================================================


class CategoriaContabilForm(_BaseForm):
    class Meta:
        model = CategoriaContabil
        fields = [
            'parent', 'nome', 'codigo', 'taxa_depreciacao_anual',
            'vida_util_padrao_meses', 'descricao',
        ]


class CentroCustoForm(_BaseForm):
    class Meta:
        model = CentroCusto
        fields = ['empresa', 'codigo', 'nome', 'departamento', 'unidade']


class LocalFisicoForm(_BaseForm):
    class Meta:
        model = LocalFisico
        fields = ['empresa', 'codigo', 'edificio', 'andar', 'sala', 'descricao']


class ResponsavelForm(_BaseForm):
    class Meta:
        model = Responsavel
        fields = ['empresa', 'user', 'nome', 'matricula', 'cargo', 'email', 'telefone']


# =============================================================================
# ATIVO
# =============================================================================


class AtivoForm(_BaseForm):
    class Meta:
        model = Ativo
        fields = [
            'empresa', 'numero_tombamento', 'descricao_detalhada', 'categoria',
            'centro_custo', 'local_fisico', 'responsavel',
            'data_aquisicao', 'valor_aquisicao', 'valor_residual',
            'vida_util_meses', 'estado_conservacao',
            'depreciavel', 'nota_fiscal', 'fornecedor', 'observacoes',
            'foto',
        ]
        widgets = {
            'data_aquisicao': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['numero_tombamento'].widget.attrs['readonly'] = True
            self.fields['numero_tombamento'].widget.attrs['class'] += (
                ' bg-gray-100 dark:bg-slate-700 cursor-not-allowed'
            )
        else:
            self.fields['numero_tombamento'].required = False
            self.fields['numero_tombamento'].widget.attrs.setdefault(
                'placeholder',
                'Deixe em branco para gerar automaticamente',
            )


# =============================================================================
# MOVIMENTAÇÃO
# =============================================================================


class MovimentacaoForm(_BaseForm):
    class Meta:
        model = Movimentacao
        fields = [
            'ativo', 'local_destino', 'responsavel_novo',
            'centro_custo_destino', 'data_movimentacao', 'motivo',
        ]
        widgets = {
            'data_movimentacao': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preencher campos de origem automaticamente
        if not self.instance.pk and 'initial' in kwargs:
            initial = kwargs['initial']
            if 'ativo' in initial:
                ativo = initial['ativo']
                if isinstance(ativo, Ativo):
                    self.initial['local_destino'] = ''
                    self.initial['responsavel_novo'] = ''


# =============================================================================
# BAIXA
# =============================================================================


class MotivoBaixaForm(_BaseForm):
    class Meta:
        model = MotivoBaixa
        fields = ['tipo', 'justificativa', 'documento_comprovante']


# =============================================================================
# INVENTÁRIO
# =============================================================================


class InventarioForm(_BaseForm):
    class Meta:
        model = Inventario
        fields = ['empresa', 'codigo', 'data_inicio', 'data_fim', 'responsavel', 'observacoes']
        widgets = {
            'data_inicio': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            ),
        }


class InventarioItemForm(_BaseForm):
    class Meta:
        model = InventarioItem
        fields = ['presenca', 'estado_conservacao_encontrado', 'observacoes']


class InventarioItemEvidenciaForm(_BaseForm):
    class Meta:
        model = InventarioItemEvidencia
        fields = ['arquivo', 'descricao']


class InventarioSobraForm(_BaseForm):
    class Meta:
        model = InventarioSobra
        fields = ['descricao_item', 'local_encontrado', 'foto', 'observacoes']


# =============================================================================
# GALERIA DE IMAGENS DO ATIVO
# =============================================================================


class AtivoImagemForm(_BaseForm):
    class Meta:
        model = AtivoImagem
        fields = ['imagem', 'descricao', 'tipo', 'principal']


# =============================================================================
# IMÓVEL
# =============================================================================


class ImovelForm(_BaseForm):
    class Meta:
        model = Imovel
        fields = [
            'empresa', 'numero_tombamento', 'descricao_detalhada', 'categoria',
            'centro_custo', 'local_fisico', 'responsavel',
            'data_aquisicao', 'valor_aquisicao', 'valor_residual',
            'vida_util_meses', 'estado_conservacao',
            'depreciavel', 'nota_fiscal', 'fornecedor', 'observacoes',
            'foto',
            # Campos específicos de imóvel
            'tipo_imovel', 'matricula_registro', 'cartorio',
            'area_total_m2', 'endereco_completo', 'numero_iptu',
        ]
        widgets = {
            'data_aquisicao': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['numero_tombamento'].widget.attrs['readonly'] = True
            self.fields['numero_tombamento'].widget.attrs['class'] += (
                ' bg-gray-100 dark:bg-slate-700 cursor-not-allowed'
            )
        else:
            self.fields['numero_tombamento'].required = False
            self.fields['numero_tombamento'].widget.attrs.setdefault(
                'placeholder',
                'Deixe em branco para gerar automaticamente',
            )


class SituacaoImovelForm(_BaseForm):
    class Meta:
        model = SituacaoImovel
        fields = ['situacao', 'data_inicio', 'data_fim', 'observacoes']
        widgets = {
            'data_inicio': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            ),
            'data_fim': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            ),
        }


# =============================================================================
# VEÍCULO
# =============================================================================


class VeiculoForm(_BaseForm):
    class Meta:
        model = Veiculo
        fields = [
            'empresa', 'numero_tombamento', 'descricao_detalhada', 'categoria',
            'centro_custo', 'local_fisico', 'responsavel',
            'data_aquisicao', 'valor_aquisicao', 'valor_residual',
            'vida_util_meses', 'estado_conservacao',
            'depreciavel', 'nota_fiscal', 'fornecedor', 'observacoes',
            'foto',
            # Campos específicos de veículo
            'placa', 'renavam', 'chassi', 'marca_modelo',
            'ano_fabricacao', 'ano_modelo', 'cor', 'combustivel',
        ]
        widgets = {
            'data_aquisicao': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['numero_tombamento'].widget.attrs['readonly'] = True
            self.fields['numero_tombamento'].widget.attrs['class'] += (
                ' bg-gray-100 dark:bg-slate-700 cursor-not-allowed'
            )
            self.fields['placa'].widget.attrs['readonly'] = True
            self.fields['placa'].widget.attrs['class'] += (
                ' bg-gray-100 dark:bg-slate-700 cursor-not-allowed'
            )
        else:
            self.fields['numero_tombamento'].required = False
            self.fields['numero_tombamento'].widget.attrs.setdefault(
                'placeholder',
                'Deixe em branco para gerar automaticamente',
            )


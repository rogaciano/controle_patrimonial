"""Django Filters para o módulo Patrimônio."""

import django_filters
from django.db import models

from .models import (
    Ativo,
    CategoriaContabil,
    CentroCusto,
    Inventario,
    LocalFisico,
    Movimentacao,
    Responsavel,
)


class AtivoFilter(django_filters.FilterSet):
    """Filtros para listagem de ativos."""

    busca = django_filters.CharFilter(
        method='filtrar_busca',
        label='Buscar',
    )
    categoria = django_filters.ModelChoiceFilter(
        queryset=CategoriaContabil.objects.filter(ativo=True),
        label='Categoria',
        empty_label='Todos',
    )
    centro_custo = django_filters.ModelChoiceFilter(
        queryset=CentroCusto.objects.filter(ativo=True),
        label='Centro de Custo',
        empty_label='Todos',
    )
    local_fisico = django_filters.ModelChoiceFilter(
        queryset=LocalFisico.objects.filter(ativo=True),
        label='Local Físico',
        empty_label='Todos',
    )
    responsavel = django_filters.ModelChoiceFilter(
        queryset=Responsavel.objects.filter(ativo=True),
        label='Responsável',
        empty_label='Todos',
    )
    status = django_filters.ChoiceFilter(
        choices=Ativo.Status.choices,
        label='Status',
        null_label='Todos',
    )
    estado_conservacao = django_filters.ChoiceFilter(
        choices=Ativo.EstadoConservacao.choices,
        label='Estado de Conservação',
        null_label='Todos',
    )
    depreciavel = django_filters.BooleanFilter(
        label='Depreciável',
    )

    class Meta:
        model = Ativo
        fields = [
            'busca', 'categoria', 'centro_custo', 'local_fisico',
            'responsavel', 'status', 'estado_conservacao', 'depreciavel',
        ]

    def filtrar_busca(self, queryset, name, value):
        return queryset.filter(
            models.Q(numero_tombamento__icontains=value)
            | models.Q(descricao_detalhada__icontains=value)
            | models.Q(nota_fiscal__icontains=value)
            | models.Q(fornecedor__icontains=value)
        )


class MovimentacaoFilter(django_filters.FilterSet):
    """Filtros para listagem de movimentações."""

    busca = django_filters.CharFilter(
        method='filtrar_busca',
        label='Buscar',
    )
    status = django_filters.ChoiceFilter(
        choices=Movimentacao.StatusMovimentacao.choices,
        label='Status',
        null_label='Todos',
    )
    data_de = django_filters.DateFilter(
        field_name='data_movimentacao',
        lookup_expr='gte',
        label='De',
    )
    data_ate = django_filters.DateFilter(
        field_name='data_movimentacao',
        lookup_expr='lte',
        label='Até',
    )

    class Meta:
        model = Movimentacao
        fields = ['busca', 'status', 'data_de', 'data_ate']

    def filtrar_busca(self, queryset, name, value):
        return queryset.filter(
            models.Q(ativo__numero_tombamento__icontains=value)
            | models.Q(motivo__icontains=value)
        )


class InventarioFilter(django_filters.FilterSet):
    """Filtros para listagem de inventários."""

    status = django_filters.ChoiceFilter(
        choices=Inventario.StatusInventario.choices,
        label='Status',
        null_label='Todos',
    )

    class Meta:
        model = Inventario
        fields = ['status']

import django_filters
from django.db import models
from .models import Empresa

class EmpresaFilter(django_filters.FilterSet):
    busca = django_filters.CharFilter(
        method='filtrar_busca',
        label='Buscar',
    )
    ativo = django_filters.BooleanFilter(
        label='Ativo D/N',
    )

    class Meta:
        model = Empresa
        fields = ['busca', 'ativo']

    def filtrar_busca(self, queryset, name, value):
        return queryset.filter(
            models.Q(nome_razao__icontains=value)
            | models.Q(nome_fantasia__icontains=value)
            | models.Q(cnpj__icontains=value)
            | models.Q(cidade__icontains=value)
        )

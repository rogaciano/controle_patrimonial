from django.contrib import admin
from apps.core.models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'matriz', 'ativo', 'cidade', 'uf')
    list_filter = ('matriz', 'ativo', 'uf')
    search_fields = ('nome_fantasia', 'nome_razao', 'cnpj')
    readonly_fields = ('criado_em', 'atualizado_em')
    

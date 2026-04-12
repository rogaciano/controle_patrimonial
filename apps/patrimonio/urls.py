"""URLs do módulo Patrimônio."""

from django.urls import path

from . import views

app_name = 'patrimonio'

urlpatterns = [
    # --- Dashboard ---
    path('', views.DashboardView.as_view(), name='dashboard'),

    # --- Ativos ---
    path('ativos/', views.AtivoListView.as_view(), name='ativo-list'),
    path('ativos/novo/', views.AtivoCreateView.as_view(), name='ativo-create'),
    path('ativos/<int:pk>/', views.AtivoDetailView.as_view(), name='ativo-detail'),
    path('ativos/<int:pk>/editar/', views.AtivoUpdateView.as_view(), name='ativo-update'),
    path('ativos/<int:pk>/status/', views.AtivoStatusUpdateView.as_view(), name='ativo-status-update'),
    path('ativos/<int:pk>/excluir/', views.AtivoDeleteView.as_view(), name='ativo-delete'),
    path('ativos/<int:pk>/auditoria/exportar/csv/', views.AtivoAuditExportCSVView.as_view(), name='ativo-auditoria-export-csv'),
    path('ativos/<int:pk>/auditoria/exportar/pdf/', views.AtivoAuditExportPDFView.as_view(), name='ativo-auditoria-export-pdf'),
    path('api/opcoes-por-empresa/<int:empresa_id>/', views.OpcõesPorEmpresaView.as_view(), name='api-opcoes-empresa'),

    # --- Galeria de Imagens ---
    path('ativos/<int:pk>/imagens/adicionar/', views.AtivoImagemCreateView.as_view(), name='ativo-imagem-create'),
    path('ativos/imagens/<int:pk>/excluir/', views.AtivoImagemDeleteView.as_view(), name='ativo-imagem-delete'),
    path('ativos/imagens/<int:pk>/principal/', views.AtivoImagemTogglePrincipalView.as_view(), name='ativo-imagem-principal'),

    # --- Categorias ---
    path('categorias/', views.CategoriaListView.as_view(), name='categoria-list'),
    path('categorias/novo/', views.CategoriaCreateView.as_view(), name='categoria-create'),
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='categoria-detail'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria-update'),

    # --- Centros de Custo ---
    path('centros-custo/', views.CentroCustoListView.as_view(), name='centrocusto-list'),
    path('centros-custo/novo/', views.CentroCustoCreateView.as_view(), name='centrocusto-create'),
    path('centros-custo/<int:pk>/editar/', views.CentroCustoUpdateView.as_view(), name='centrocusto-update'),

    # --- Locais Físicos ---
    path('locais/', views.LocalFisicoListView.as_view(), name='localfisico-list'),
    path('locais/novo/', views.LocalFisicoCreateView.as_view(), name='localfisico-create'),
    path('locais/<int:pk>/editar/', views.LocalFisicoUpdateView.as_view(), name='localfisico-update'),

    # --- Responsáveis ---
    path('responsaveis/', views.ResponsavelListView.as_view(), name='responsavel-list'),
    path('responsaveis/novo/', views.ResponsavelCreateView.as_view(), name='responsavel-create'),
    path('responsaveis/<int:pk>/editar/', views.ResponsavelUpdateView.as_view(), name='responsavel-update'),

    # --- Movimentações ---
    path('movimentacoes/', views.MovimentacaoListView.as_view(), name='movimentacao-list'),
    path('movimentacoes/novo/', views.MovimentacaoCreateView.as_view(), name='movimentacao-create'),
    path('movimentacoes/<int:pk>/aprovar/', views.MovimentacaoAprovarView.as_view(), name='movimentacao-aprovar'),
    path('movimentacoes/<int:pk>/concluir/', views.MovimentacaoConcluirView.as_view(), name='movimentacao-concluir'),
    path('movimentacoes/<int:pk>/cancelar/', views.MovimentacaoCancelarView.as_view(), name='movimentacao-cancelar'),

    # --- Inventários ---
    path('inventarios/', views.InventarioListView.as_view(), name='inventario-list'),
    path('inventarios/novo/', views.InventarioCreateView.as_view(), name='inventario-create'),
    path('inventarios/<int:pk>/', views.InventarioDetailView.as_view(), name='inventario-detail'),
    path('inventarios/<int:pk>/gerar-snapshot/', views.InventarioGerarSnapshotView.as_view(), name='inventario-gerar-snapshot'),
    path('inventarios/item/<int:pk>/toggle/', views.InventarioItemToggleView.as_view(), name='inventario-item-toggle'),
    path('inventarios/item/<int:pk>/evidencias/', views.InventarioItemEvidenciaListView.as_view(), name='inventario-item-evidencias'),
    path('inventarios/item/<int:pk>/evidencias/avaria/', views.InventarioItemEvidenciaCreateView.as_view(), name='inventario-item-evidencia-avaria-create'),
    path('inventarios/<int:pk>/finalizar/', views.InventarioFinalizarView.as_view(), name='inventario-finalizar'),

    # --- Depreciação ---
    path('depreciacao/processar/', views.ProcessarDepreciacaoView.as_view(), name='depreciacao-processar'),

    # --- Imóveis ---
    path('imoveis/', views.ImovelListView.as_view(), name='imovel-list'),
    path('imoveis/novo/', views.ImovelCreateView.as_view(), name='imovel-create'),
    path('imoveis/<int:pk>/', views.ImovelDetailView.as_view(), name='imovel-detail'),
    path('imoveis/<int:pk>/editar/', views.ImovelUpdateView.as_view(), name='imovel-update'),
    path('imoveis/<int:pk>/excluir/', views.ImovelDeleteView.as_view(), name='imovel-delete'),
    path('imoveis/<int:pk>/situacao/', views.SituacaoImovelCreateView.as_view(), name='imovel-situacao-create'),

    # --- Veículos ---
    path('veiculos/', views.VeiculoListView.as_view(), name='veiculo-list'),
    path('veiculos/novo/', views.VeiculoCreateView.as_view(), name='veiculo-create'),
    path('veiculos/<int:pk>/', views.VeiculoDetailView.as_view(), name='veiculo-detail'),
    path('veiculos/<int:pk>/editar/', views.VeiculoUpdateView.as_view(), name='veiculo-update'),
    path('veiculos/<int:pk>/excluir/', views.VeiculoDeleteView.as_view(), name='veiculo-delete'),
]


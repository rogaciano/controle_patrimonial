from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('empresas/', views.EmpresaListView.as_view(), name='empresa-list'),
    path('empresas/nova/', views.EmpresaCreateView.as_view(), name='empresa-create'),
    path('empresas/<int:pk>/', views.EmpresaDetailView.as_view(), name='empresa-detail'),
    path('empresas/<int:pk>/editar/', views.EmpresaUpdateView.as_view(), name='empresa-update'),
]

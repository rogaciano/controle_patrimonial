from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django_filters.views import FilterView
from django.db.models import Sum

from .models import Empresa
from .forms import EmpresaForm
from .filters import EmpresaFilter

# Import ativo to get the statistics
from apps.patrimonio.models import Ativo, LocalFisico, CentroCusto, Responsavel

class EmpresaListView(LoginRequiredMixin, FilterView):
    model = Empresa
    template_name = 'core/empresa_list.html'
    context_object_name = 'itens'
    paginate_by = 20
    filterset_class = EmpresaFilter

    def get_queryset(self):
        return Empresa.objects.all().order_by('nome_fantasia')


class EmpresaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'core/empresa_form.html'
    success_url = reverse_lazy('core:empresa-list')
    success_message = 'Empresa criada com sucesso!'


class EmpresaUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'core/empresa_form.html'
    success_url = reverse_lazy('core:empresa-list')
    success_message = 'Empresa atualizada com sucesso!'


class EmpresaDetailView(LoginRequiredMixin, DetailView):
    model = Empresa
    template_name = 'core/empresa_detail.html'
    context_object_name = 'empresa'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        empresa = self.object

        # KPIs and Statistics
        ativos = Ativo.objects.filter(empresa=empresa, ativo=True)
        ctx['total_ativos'] = ativos.count()
        ctx['valor_total'] = ativos.aggregate(
            total=Sum('valor_aquisicao')
        )['total'] or 0.00
        
        ctx['total_locais'] = LocalFisico.objects.filter(empresa=empresa, ativo=True).count()
        ctx['total_centros'] = CentroCusto.objects.filter(empresa=empresa, ativo=True).count()
        ctx['total_responsaveis'] = Responsavel.objects.filter(empresa=empresa, ativo=True).count()
        
        return ctx

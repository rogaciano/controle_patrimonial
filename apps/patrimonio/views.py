"""
Views do módulo Patrimônio.

Dashboard + CRUDs + Ações (movimentação, inventário, depreciação).
"""

import json
import logging
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models, transaction
from django.db.models import Count, F, Q, Subquery, Sum, OuterRef
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from django_filters.views import FilterView

from .filters import AtivoFilter, InventarioFilter, MovimentacaoFilter
from .forms import (
    AtivoForm,
    CategoriaContabilForm,
    CentroCustoForm,
    InventarioForm,
    LocalFisicoForm,
    MotivoBaixaForm,
    MovimentacaoForm,
    ResponsavelForm,
)
from .models import (
    Ativo,
    CategoriaContabil,
    CentroCusto,
    DepreciacaoRegistro,
    Inventario,
    InventarioItem,
    LocalFisico,
    Movimentacao,
    Responsavel,
)
from . import services

logger = logging.getLogger('apps.patrimonio')


# =============================================================================
# DASHBOARD
# =============================================================================


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal com KPIs patrimoniais."""

    template_name = 'patrimonio/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ativos_qs = Ativo.objects.filter(ativo=True).exclude(status='BAIXADO')

        # KPI 1: Valor Total
        ctx['valor_total_aquisicao'] = ativos_qs.aggregate(
            total=Sum('valor_aquisicao')
        )['total'] or Decimal('0.00')

        # Valor contábil atual (último registro fiscal de cada ativo)
        ultimo_depr = DepreciacaoRegistro.objects.filter(
            ativo=OuterRef('pk'), cenario='FISCAL'
        ).order_by('-ano_referencia', '-mes_referencia')

        ativos_com_nbv = ativos_qs.annotate(
            nbv=Subquery(ultimo_depr.values('valor_contabil_atual')[:1])
        )
        # Para total, somar NBV ou valor de aquisição se nunca depreciado
        total_nbv = Decimal('0.00')
        for a in ativos_com_nbv:
            total_nbv += a.nbv if a.nbv is not None else a.valor_aquisicao
        ctx['valor_total_atual'] = total_nbv
        ctx['depreciacao_total'] = ctx['valor_total_aquisicao'] - total_nbv

        # KPI 2: Status dos bens
        ctx['status_distribuicao'] = list(
            ativos_qs.values('status').annotate(
                total=Count('id')
            ).order_by('status')
        )

        # KPI 3: Conservação
        ctx['conservacao_distribuicao'] = list(
            ativos_qs.values('estado_conservacao').annotate(
                total=Count('id')
            ).order_by('estado_conservacao')
        )

        # KPI 4: Depreciação mensal (últimos 12 meses)
        ctx['depreciacao_mensal'] = list(
            DepreciacaoRegistro.objects.filter(
                cenario='FISCAL',
            ).values(
                'ano_referencia', 'mes_referencia'
            ).annotate(
                total_mes=Sum('valor_depreciado_mes')
            ).order_by('ano_referencia', 'mes_referencia')[:12]
        )

        # KPI 5: Último inventário
        ultimo_inventario = Inventario.objects.filter(
            status='CONCLUIDO', ativo=True
        ).order_by('-data_fim').first()

        if ultimo_inventario:
            ctx['ultimo_inventario'] = ultimo_inventario
            ctx['inv_nao_localizados'] = ultimo_inventario.itens.filter(
                presenca='NAO_LOCALIZADO'
            ).count()
            ctx['inv_localizados'] = ultimo_inventario.itens.filter(
                presenca='LOCALIZADO'
            ).count()
            ctx['inv_sobras'] = ultimo_inventario.sobras.count()
            total_itens = ultimo_inventario.itens.count()
            ctx['inv_taxa_conformidade'] = (
                round(ctx['inv_localizados'] / total_itens * 100, 1)
                if total_itens > 0
                else 0
            )

        # Contadores gerais
        ctx['total_ativos'] = ativos_qs.count()
        ctx['valor_total'] = ctx['valor_total_aquisicao']
        ctx['total_baixados'] = Ativo.objects.filter(
            ativo=True, status='BAIXADO'
        ).count()
        ctx['movimentacoes_pendentes'] = Movimentacao.objects.filter(
            status__in=['SOLICITADA', 'APROVADA']
        ).count()

        # Chart data — JSON for Chart.js
        status_labels = {
            'ATIVO': 'Ativo', 'EM_MANUTENCAO': 'Manutenção',
            'BAIXADO': 'Baixado', 'CEDIDO': 'Cedido',
        }
        status_data = [
            {'label': status_labels.get(s['status'], s['status']), 'count': s['total']}
            for s in ctx['status_distribuicao']
        ]
        ctx['status_data'] = json.dumps(status_data)

        cat_counts = list(
            ativos_qs.values('categoria__nome')
            .annotate(total=Count('id'))
            .order_by('-total')[:8]
        )
        categoria_data = [
            {'label': c['categoria__nome'], 'count': c['total']}
            for c in cat_counts
        ]
        ctx['categoria_data'] = json.dumps(categoria_data)

        return ctx


# =============================================================================
# ATIVOS — CRUD
# =============================================================================


class AtivoListView(LoginRequiredMixin, FilterView):
    """Listagem de ativos com filtros e paginação."""

    model = Ativo
    template_name = 'patrimonio/ativo_list.html'
    context_object_name = 'itens'
    paginate_by = 20
    filterset_class = AtivoFilter

    def get_queryset(self):
        return (
            Ativo.objects.filter(ativo=True)
            .select_related('categoria', 'centro_custo', 'local_fisico', 'responsavel')
            .order_by('-criado_em')
        )


class AtivoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Cadastro de novo ativo."""

    model = Ativo
    form_class = AtivoForm
    template_name = 'patrimonio/ativo_form.html'
    success_url = reverse_lazy('patrimonio:ativo-list')
    success_message = 'Ativo cadastrado com sucesso!'

    @transaction.atomic
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            logger.error('Erro ao criar ativo: %s', e)
            messages.error(self.request, f'Erro ao criar ativo: {e}')
            return self.form_invalid(form)


class AtivoDetailView(LoginRequiredMixin, DetailView):
    """Detalhes do ativo com depreciação e movimentações."""

    model = Ativo
    template_name = 'patrimonio/ativo_detail.html'
    context_object_name = 'ativo'

    def get_queryset(self):
        return Ativo.objects.select_related(
            'categoria', 'centro_custo', 'local_fisico', 'responsavel'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ativo = self.object
        ctx['depreciacoes'] = ativo.depreciacoes.filter(
            cenario='FISCAL'
        ).order_by('-ano_referencia', '-mes_referencia')[:12]
        ctx['movimentacoes'] = ativo.movimentacoes.select_related(
            'local_origem', 'local_destino',
            'responsavel_anterior', 'responsavel_novo',
        ).order_by('-data_movimentacao')[:10]
        ctx['inventario_itens'] = ativo.itens_inventario.select_related(
            'inventario', 'inventario__responsavel'
        ).order_by('-inventario__data_inicio')
        ctx['baixa_form'] = MotivoBaixaForm()
        return ctx


class AtivoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Edição de ativo existente."""

    model = Ativo
    form_class = AtivoForm
    template_name = 'patrimonio/ativo_form.html'
    success_url = reverse_lazy('patrimonio:ativo-list')
    success_message = 'Ativo atualizado com sucesso!'


class AtivoDeleteView(LoginRequiredMixin, DeleteView):
    """Exclusão (soft delete) de ativo."""

    model = Ativo
    success_url = reverse_lazy('patrimonio:ativo-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(request, 'Ativo removido com sucesso.')
        return redirect(self.success_url)


# =============================================================================
# CADASTROS AUXILIARES — CRUDs Simples
# =============================================================================


class CategoriaListView(LoginRequiredMixin, ListView):
    model = CategoriaContabil
    template_name = 'patrimonio/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        return CategoriaContabil.objects.filter(ativo=True).select_related('parent')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Categorias Contábeis'
        ctx['create_url'] = reverse_lazy('patrimonio:categoria-create')
        ctx['detail_url_name'] = 'patrimonio:categoria-detail'
        ctx['update_url_name'] = 'patrimonio:categoria-update'
        return ctx


class CategoriaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = CategoriaContabil
    form_class = CategoriaContabilForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:categoria-list')
    success_message = 'Categoria criada com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Categoria Contábil'
        ctx['back_url'] = reverse_lazy('patrimonio:categoria-list')
        return ctx


class CategoriaDetailView(LoginRequiredMixin, DetailView):
    model = CategoriaContabil
    template_name = 'patrimonio/categoria_detail.html'
    context_object_name = 'categoria'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['ativos'] = self.object.ativos.select_related(
            'local_fisico', 'responsavel'
        ).order_by('numero_tombamento')
        return ctx


class CategoriaUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CategoriaContabil
    form_class = CategoriaContabilForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:categoria-list')
    success_message = 'Categoria atualizada com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Categoria Contábil'
        ctx['back_url'] = reverse_lazy('patrimonio:categoria-list')
        return ctx


class CentroCustoListView(LoginRequiredMixin, ListView):
    model = CentroCusto
    template_name = 'patrimonio/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        return CentroCusto.objects.filter(ativo=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Centros de Custo'
        ctx['create_url'] = reverse_lazy('patrimonio:centrocusto-create')
        ctx['update_url_name'] = 'patrimonio:centrocusto-update'
        return ctx


class CentroCustoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = CentroCusto
    form_class = CentroCustoForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:centrocusto-list')
    success_message = 'Centro de Custo criado com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Centro de Custo'
        ctx['back_url'] = reverse_lazy('patrimonio:centrocusto-list')
        return ctx


class CentroCustoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CentroCusto
    form_class = CentroCustoForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:centrocusto-list')
    success_message = 'Centro de Custo atualizado com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Centro de Custo'
        ctx['back_url'] = reverse_lazy('patrimonio:centrocusto-list')
        return ctx


class LocalFisicoListView(LoginRequiredMixin, ListView):
    model = LocalFisico
    template_name = 'patrimonio/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        return LocalFisico.objects.filter(ativo=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Locais Físicos'
        ctx['create_url'] = reverse_lazy('patrimonio:localfisico-create')
        ctx['update_url_name'] = 'patrimonio:localfisico-update'
        return ctx


class LocalFisicoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = LocalFisico
    form_class = LocalFisicoForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:localfisico-list')
    success_message = 'Local Físico criado com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Local Físico'
        ctx['back_url'] = reverse_lazy('patrimonio:localfisico-list')
        return ctx


class LocalFisicoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = LocalFisico
    form_class = LocalFisicoForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:localfisico-list')
    success_message = 'Local Físico atualizado com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Local Físico'
        ctx['back_url'] = reverse_lazy('patrimonio:localfisico-list')
        return ctx


class ResponsavelListView(LoginRequiredMixin, ListView):
    model = Responsavel
    template_name = 'patrimonio/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        return Responsavel.objects.filter(ativo=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Responsáveis'
        ctx['create_url'] = reverse_lazy('patrimonio:responsavel-create')
        ctx['update_url_name'] = 'patrimonio:responsavel-update'
        return ctx


class ResponsavelCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Responsavel
    form_class = ResponsavelForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:responsavel-list')
    success_message = 'Responsável criado com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Responsável'
        ctx['back_url'] = reverse_lazy('patrimonio:responsavel-list')
        return ctx


class ResponsavelUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Responsavel
    form_class = ResponsavelForm
    template_name = 'patrimonio/generic_form.html'
    success_url = reverse_lazy('patrimonio:responsavel-list')
    success_message = 'Responsável atualizado com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Responsável'
        ctx['back_url'] = reverse_lazy('patrimonio:responsavel-list')
        return ctx


# =============================================================================
# MOVIMENTAÇÕES
# =============================================================================


class MovimentacaoListView(LoginRequiredMixin, FilterView):
    model = Movimentacao
    template_name = 'patrimonio/movimentacao_list.html'
    context_object_name = 'itens'
    paginate_by = 20
    filterset_class = MovimentacaoFilter

    def get_queryset(self):
        return (
            Movimentacao.objects.filter(ativo__ativo=True)
            .select_related(
                'ativo', 'local_origem', 'local_destino',
                'responsavel_anterior', 'responsavel_novo',
            )
            .order_by('-data_movimentacao')
        )


class MovimentacaoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = 'patrimonio/movimentacao_form.html'
    success_url = reverse_lazy('patrimonio:movimentacao-list')
    success_message = 'Movimentação solicitada com sucesso!'

    def form_valid(self, form):
        mov = form.save(commit=False)
        ativo = mov.ativo
        # Auto-preencher campos de origem
        mov.local_origem = ativo.local_fisico
        mov.responsavel_anterior = ativo.responsavel
        mov.centro_custo_origem = ativo.centro_custo
        mov.status = 'SOLICITADA'
        mov.save()
        return redirect(self.success_url)


class MovimentacaoAprovarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mov = get_object_or_404(Movimentacao, pk=pk)
        try:
            services.aprovar_movimentacao(mov, request.user)
            messages.success(request, 'Movimentação aprovada com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao aprovar: {e}')
        return redirect('patrimonio:movimentacao-list')


class MovimentacaoConcluirView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mov = get_object_or_404(Movimentacao, pk=pk)
        try:
            services.concluir_movimentacao(mov)
            messages.success(request, 'Movimentação concluída. Ativo atualizado.')
        except Exception as e:
            messages.error(request, f'Erro ao concluir: {e}')
        return redirect('patrimonio:movimentacao-list')


class MovimentacaoCancelarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mov = get_object_or_404(Movimentacao, pk=pk)
        try:
            services.cancelar_movimentacao(mov)
            messages.success(request, 'Movimentação cancelada.')
        except Exception as e:
            messages.error(request, f'Erro ao cancelar: {e}')
        return redirect('patrimonio:movimentacao-list')


# =============================================================================
# INVENTÁRIO
# =============================================================================


class InventarioListView(LoginRequiredMixin, FilterView):
    model = Inventario
    template_name = 'patrimonio/inventario_list.html'
    context_object_name = 'itens'
    paginate_by = 20
    filterset_class = InventarioFilter

    def get_queryset(self):
        return (
            Inventario.objects.filter(ativo=True)
            .select_related('responsavel')
            .order_by('-data_inicio')
        )


class InventarioCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Inventario
    form_class = InventarioForm
    template_name = 'patrimonio/inventario_form.html'
    success_url = reverse_lazy('patrimonio:inventario-list')
    success_message = 'Inventário criado com sucesso!'


class InventarioDetailView(LoginRequiredMixin, DetailView):
    model = Inventario
    template_name = 'patrimonio/inventario_detail.html'
    context_object_name = 'inventario'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inv = self.object
        itens = inv.itens.select_related('ativo').order_by('ativo__numero_tombamento')

        # Filtros
        status_filter = self.request.GET.get('status')
        if status_filter:
            itens = itens.filter(presenca=status_filter)

        ctx['itens'] = itens
        ctx['status_filter'] = status_filter
        ctx['is_filtered_localizado'] = (status_filter == 'LOCALIZADO')
        ctx['is_filtered_nao_localizado'] = (status_filter == 'NAO_LOCALIZADO')
        
        ctx['sobras'] = inv.sobras.all()
        ctx['localizados'] = inv.itens.filter(presenca='LOCALIZADO').count()
        ctx['nao_localizados'] = inv.itens.filter(presenca='NAO_LOCALIZADO').count()
        total = inv.itens.count()
        ctx['total_itens'] = total
        ctx['taxa_conformidade'] = (
            round(ctx['localizados'] / total * 100, 1) if total > 0 else 0
        )
        return ctx


class InventarioGerarSnapshotView(LoginRequiredMixin, View):
    def post(self, request, pk):
        inv = get_object_or_404(Inventario, pk=pk)
        try:
            total = services.gerar_snapshot_inventario(inv)
            messages.success(
                request,
                f'Snapshot gerado com sucesso! {total} ativos adicionados.',
            )
        except Exception as e:
            messages.error(request, f'Erro ao gerar snapshot: {e}')
        return redirect('patrimonio:inventario-detail', pk=pk)


class InventarioItemToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(InventarioItem, pk=pk)
        if item.presenca == 'NAO_LOCALIZADO':
            item.presenca = 'LOCALIZADO'
            # Tentar manter estado de conservação do ativo se não foi informado
            if not item.estado_conservacao_encontrado:
                item.estado_conservacao_encontrado = item.ativo.estado_conservacao
            msg = 'Item marcado como LOCALIZADO.'
        else:
            item.presenca = 'NAO_LOCALIZADO'
            msg = 'Item marcado como NÃO LOCALIZADO.'
        
        item.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'presenca': item.presenca,
                'message': msg
            })

        messages.success(request, msg)
        return redirect(
            reverse_lazy('patrimonio:inventario-detail', kwargs={'pk': item.inventario.pk}) + f'#item-{item.pk}'
        )


class InventarioFinalizarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        inv = get_object_or_404(Inventario, pk=pk)
        try:
            resultado = services.finalizar_inventario(inv)
            messages.success(
                request,
                f'Inventário finalizado! '
                f'Localizados: {resultado["localizados"]}, '
                f'Não localizados: {resultado["nao_localizados"]}, '
                f'Taxa: {resultado["taxa_conformidade"]}%',
            )
        except Exception as e:
            messages.error(request, f'Erro ao finalizar: {e}')
        return redirect('patrimonio:inventario-detail', pk=pk)


# =============================================================================
# DEPRECIAÇÃO
# =============================================================================


class ProcessarDepreciacaoView(LoginRequiredMixin, TemplateView):
    """Processa depreciação mensal em lote."""

    template_name = 'patrimonio/processar_depreciacao.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['ano'] = date.today().year
        ctx['mes'] = date.today().month
        return ctx

    def post(self, request, *args, **kwargs):
        ano = int(request.POST.get('ano', date.today().year))
        mes = int(request.POST.get('mes', date.today().month))
        cenario = request.POST.get('cenario', 'FISCAL')

        try:
            resultado = services.processar_depreciacao_lote(ano, mes, cenario)
            messages.success(
                request,
                f'Depreciação {mes:02d}/{ano} ({cenario}) processada! '
                f'{resultado["processados"]} ativos depreciados, '
                f'{resultado["ignorados"]} ignorados.',
            )
            if resultado['erros']:
                messages.warning(
                    request,
                    f'{len(resultado["erros"])} erros encontrados. '
                    'Verifique os logs.',
                )
        except Exception as e:
            messages.error(request, f'Erro ao processar depreciação: {e}')

        return redirect('patrimonio:dashboard')

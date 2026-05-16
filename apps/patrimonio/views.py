"""
Views do módulo Patrimônio.

Dashboard + CRUDs + Ações (movimentação, inventário, depreciação).
"""

import json
import logging
import csv
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.db.models import Count, F, Q, Subquery, Sum, OuterRef, Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
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
from auditlog.models import LogEntry

from .filters import (
    AtivoFilter,
    CentroCustoFilter,
    ImovelFilter,
    InventarioFilter,
    InventarioItemFilter,
    LocalFisicoFilter,
    MovimentacaoFilter,
    ResponsavelFilter,
    VeiculoFilter,
)
from .forms import (
    AtivoForm,
    AtivoImagemForm,
    CategoriaContabilForm,
    CentroCustoForm,
    ImovelForm,
    InventarioForm,
    InventarioItemEvidenciaForm,
    LocalFisicoForm,
    MotivoBaixaForm,
    MovimentacaoForm,
    ResponsavelForm,
    SituacaoImovelForm,
    VeiculoForm,
)
from .models import (
    Ativo,
    AtivoImagem,
    CategoriaContabil,
    CentroCusto,
    DepreciacaoRegistro,
    Imovel,
    Inventario,
    InventarioItem,
    InventarioItemEvidencia,
    LocalFisico,
    MotivoBaixa,
    Movimentacao,
    Responsavel,
    SituacaoImovel,
    Veiculo,
)
from . import services

logger = logging.getLogger('apps.patrimonio')


def _user_can_access_asset_audit(user) -> bool:
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def _action_label(action: int) -> str:
    create_action = getattr(LogEntry.Action, 'CREATE', 0)
    update_action = getattr(LogEntry.Action, 'UPDATE', 1)
    delete_action = getattr(LogEntry.Action, 'DELETE', 2)
    access_action = getattr(LogEntry.Action, 'ACCESS', 3)
    return {
        create_action: 'Criação',
        update_action: 'Atualização',
        delete_action: 'Exclusão',
        access_action: 'Acesso',
    }.get(action, 'Evento')


def _resolve_field_value(model_class, field_name: str, value):
    if value in (None, '', 'None'):
        return '—'
    try:
        field = model_class._meta.get_field(field_name)
    except Exception:
        return str(value)

    if not field.is_relation:
        return str(value)

    lookup_value = value
    if isinstance(value, str) and value.isdigit():
        lookup_value = int(value)
    elif not isinstance(value, int):
        return str(value)

    related_model = field.remote_field.model
    related = related_model.objects.filter(pk=lookup_value).first()
    return str(related) if related else str(value)


def _extract_entry_changes(entry: LogEntry) -> dict:
    changes = entry.changes_dict if hasattr(entry, 'changes_dict') else entry.changes
    if not isinstance(changes, dict):
        return {}
    return changes


def _get_asset_audit_entries_queryset(ativo: Ativo):
    ativo_ct = ContentType.objects.get_for_model(Ativo)
    mov_ct = ContentType.objects.get_for_model(Movimentacao)
    img_ct = ContentType.objects.get_for_model(AtivoImagem)
    baixa_ct = ContentType.objects.get_for_model(MotivoBaixa)

    movimentacao_ids = list(
        Movimentacao.objects.filter(ativo=ativo).values_list('pk', flat=True)
    )
    imagem_ids = list(
        AtivoImagem.objects.filter(ativo=ativo).values_list('pk', flat=True)
    )
    baixa = MotivoBaixa.objects.filter(ativo=ativo).first()

    query = Q(content_type=ativo_ct, object_id=ativo.pk)
    if movimentacao_ids:
        query |= Q(content_type=mov_ct, object_id__in=movimentacao_ids)
    if imagem_ids:
        query |= Q(content_type=img_ct, object_id__in=imagem_ids)
    if baixa:
        query |= Q(content_type=baixa_ct, object_id=baixa.pk)

    return LogEntry.objects.select_related('actor', 'content_type').filter(query)


def _get_auditoria_filters_from_request(request) -> dict:
    actor_id = request.GET.get('aud_actor', '').strip()
    start_raw = request.GET.get('aud_start', '').strip()
    end_raw = request.GET.get('aud_end', '').strip()

    actor_id = actor_id if actor_id.isdigit() else ''
    start_date = parse_date(start_raw) if start_raw else None
    end_date = parse_date(end_raw) if end_raw else None

    querystring = urlencode({
        k: v for k, v in {
            'aud_actor': actor_id,
            'aud_start': start_raw if start_date else '',
            'aud_end': end_raw if end_date else '',
        }.items() if v
    })

    return {
        'actor_id': actor_id,
        'start_date': start_date,
        'end_date': end_date,
        'start_raw': start_raw if start_date else '',
        'end_raw': end_raw if end_date else '',
        'querystring': querystring,
    }


def _build_asset_audit_timeline(
    ativo: Ativo,
    limit: int | None = None,
    actor_id: str = '',
    start_date=None,
    end_date=None,
) -> list[dict]:
    entries = _get_asset_audit_entries_queryset(ativo)

    if actor_id:
        entries = entries.filter(actor_id=int(actor_id))
    if start_date:
        entries = entries.filter(timestamp__date__gte=start_date)
    if end_date:
        entries = entries.filter(timestamp__date__lte=end_date)

    entries = entries.order_by('-timestamp')
    if limit:
        entries = entries[:limit]

    events: list[dict] = []
    for entry in entries:
        model_class = entry.content_type.model_class()
        model_label = (
            model_class._meta.verbose_name.title()
            if model_class is not None
            else entry.content_type.name.title()
        )
        actor = entry.actor.get_username() if entry.actor else 'Sistema'
        action = _action_label(entry.action)
        changes = _extract_entry_changes(entry)

        if not changes:
            events.append({
                'timestamp': entry.timestamp,
                'actor': actor,
                'origem': model_label,
                'acao': action,
                'campo': '—',
                'antes': '—',
                'depois': '—',
            })
            continue

        for field_name, value_pair in changes.items():
            if isinstance(value_pair, (list, tuple)) and len(value_pair) == 2:
                old_value, new_value = value_pair
            else:
                old_value, new_value = None, value_pair

            field_label = field_name
            if model_class is not None:
                try:
                    field_label = model_class._meta.get_field(field_name).verbose_name
                except Exception:
                    pass

            events.append({
                'timestamp': entry.timestamp,
                'actor': actor,
                'origem': model_label,
                'acao': action,
                'campo': str(field_label).title(),
                'antes': (
                    _resolve_field_value(model_class, field_name, old_value)
                    if model_class is not None
                    else str(old_value)
                ),
                'depois': (
                    _resolve_field_value(model_class, field_name, new_value)
                    if model_class is not None
                    else str(new_value)
                ),
            })

    return events


def _pdf_escape(text: str) -> str:
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _build_simple_pdf(lines: list[str], title: str) -> bytes:
    lines_per_page = 45
    pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
    if not pages:
        pages = [[]]

    objects: list[str] = []
    objects.append('<< /Type /Catalog /Pages 2 0 R >>')

    page_count = len(pages)
    page_obj_numbers = [3 + idx * 2 for idx in range(page_count)]
    content_obj_numbers = [4 + idx * 2 for idx in range(page_count)]
    font_obj_number = 3 + page_count * 2

    kids_ref = ' '.join(f'{num} 0 R' for num in page_obj_numbers)
    objects.append(f'<< /Type /Pages /Kids [{kids_ref}] /Count {page_count} >>')

    for idx, page_lines in enumerate(pages):
        page_obj = (
            f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
            f'/Resources << /Font << /F1 {font_obj_number} 0 R >> >> '
            f'/Contents {content_obj_numbers[idx]} 0 R >>'
        )

        commands = [f'BT /F1 12 Tf 40 805 Td ({_pdf_escape(title)}) Tj ET']
        y = 785
        for line in page_lines:
            commands.append(f'BT /F1 9 Tf 40 {y} Td ({_pdf_escape(line)}) Tj ET')
            y -= 16

        stream = '\n'.join(commands)
        stream_bytes = stream.encode('latin-1', errors='replace')
        content_obj = (
            f'<< /Length {len(stream_bytes)} >>\n'
            f'stream\n{stream}\nendstream'
        )

        objects.append(page_obj)
        objects.append(content_obj)

    objects.append('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')

    output = '%PDF-1.4\n'
    offsets = [0]

    for obj_number, obj_content in enumerate(objects, start=1):
        offsets.append(len(output.encode('latin-1', errors='replace')))
        output += f'{obj_number} 0 obj\n{obj_content}\nendobj\n'

    xref_position = len(output.encode('latin-1', errors='replace'))
    output += f'xref\n0 {len(objects) + 1}\n'
    output += '0000000000 65535 f \n'
    for off in offsets[1:]:
        output += f'{off:010} 00000 n \n'

    output += (
        f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n'
        f'startxref\n{xref_position}\n%%EOF'
    )
    return output.encode('latin-1', errors='replace')


# =============================================================================
# DASHBOARD
# =============================================================================


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal com KPIs patrimoniais."""

    template_name = 'patrimonio/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        empresa_id = self.request.GET.get('empresa')
        ativos_qs = Ativo.objects.filter(ativo=True).exclude(status='BAIXADO')
        
        if empresa_id:
            ativos_qs = ativos_qs.filter(empresa_id=empresa_id)

        from apps.core.models import Empresa
        ctx['empresas'] = Empresa.objects.filter(ativo=True)
        ctx['empresa_selecionada'] = int(empresa_id) if empresa_id and empresa_id.isdigit() else None

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

        local_rows = list(
            ativos_qs.values(
                'local_fisico_id',
                'local_fisico__edificio',
                'local_fisico__andar',
                'local_fisico__sala',
            )
            .annotate(
                total=Count('id'),
                valor=Sum('valor_aquisicao'),
            )
            .order_by('-total')
        )

        def _local_label(row: dict) -> str:
            if not row.get('local_fisico_id'):
                return 'Sem local'
            parts = [row.get('local_fisico__edificio') or '']
            andar = (row.get('local_fisico__andar') or '').strip()
            sala = (row.get('local_fisico__sala') or '').strip()
            if andar:
                parts.append(andar)
            if sala:
                parts.append(sala)
            return ' / '.join([p for p in parts if p]) or 'Sem local'

        local_qtd_data = [
            {
                'label': _local_label(r),
                'count': r['total'],
            }
            for r in local_rows
            if r['total']
        ]

        local_valor_data = [
            {
                'label': _local_label(r),
                'value': float(r['valor'] or 0),
            }
            for r in local_rows
            if r['valor']
        ]

        ctx['local_qtd_data'] = json.dumps(local_qtd_data)
        ctx['local_valor_data'] = json.dumps(local_valor_data)

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



class CloneAtivoMixin:
    def get_initial(self):
        initial = super().get_initial()
        clone_id = self.request.GET.get('clone')
        if clone_id:
            try:
                obj = self.model.objects.get(pk=clone_id)
                for field in obj._meta.fields:
                    if field.primary_key or field.name.endswith('_ptr') or field.name in ['numero_tombamento', 'criado_em', 'atualizado_em', 'id']:
                        continue
                    initial[field.name] = getattr(obj, field.attname)
                
                from django.utils import timezone
                initial['data_aquisicao'] = timezone.now().date()
            except self.model.DoesNotExist:
                pass
        return initial

class AtivoCreateView(LoginRequiredMixin, SuccessMessageMixin, CloneAtivoMixin, CreateView):
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
        ctx['inventario_itens'] = (
            ativo.itens_inventario.select_related(
                'inventario', 'inventario__responsavel', 'confirmado_por'
            )
            .prefetch_related(
                Prefetch(
                    'evidencias',
                    queryset=InventarioItemEvidencia.objects.select_related('criado_por').order_by('-criado_em'),
                    to_attr='evidencias_list',
                )
            )
            .order_by('-inventario__data_inicio')
        )
        ctx['baixa_form'] = MotivoBaixaForm()
        # Galeria de imagens
        ctx['imagens'] = ativo.imagens.order_by('-principal', '-criado_em')
        ctx['imagem_form'] = AtivoImagemForm()
        status_transicoes = services.status_transicoes_permitidas_para_usuario(
            ativo.status,
            self.request.user,
        )
        ctx['can_change_asset_status'] = bool(status_transicoes)
        status_labels = dict(Ativo.Status.choices)
        ctx['status_transicoes_permitidas'] = status_transicoes
        ctx['status_transicoes_permitidas_display'] = [
            (status_value, status_labels.get(status_value, status_value))
            for status_value in status_transicoes
        ]
        ctx['status_transicoes_config'] = [
            {
                'value': status_destino,
                'label': status_labels.get(status_destino, status_destino),
                'motivos': services.status_motivos_disponiveis(status_destino),
            }
            for status_destino in status_transicoes
        ]
        ctx['status_historico'] = ativo.historico_status.select_related('alterado_por')[:20]
        ctx['can_view_auditoria'] = _user_can_access_asset_audit(self.request.user)
        if ctx['can_view_auditoria']:
            filtros = _get_auditoria_filters_from_request(self.request)
            audit_entries = _get_asset_audit_entries_queryset(ativo)
            User = get_user_model()
            actor_ids = audit_entries.filter(actor__isnull=False).values_list(
                'actor_id', flat=True
            ).distinct()
            ctx['auditoria_atores'] = User.objects.filter(pk__in=actor_ids).order_by('username')
            ctx['auditoria_filtros'] = {
                'actor_id': filtros['actor_id'],
                'start_raw': filtros['start_raw'],
                'end_raw': filtros['end_raw'],
            }
            ctx['auditoria_querystring'] = filtros['querystring']
            ctx['auditoria_eventos'] = _build_asset_audit_timeline(
                ativo,
                limit=120,
                actor_id=filtros['actor_id'],
                start_date=filtros['start_date'],
                end_date=filtros['end_date'],
            )
        return ctx


class AtivoAuditExportCSVView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if not _user_can_access_asset_audit(request.user):
            raise PermissionDenied('Acesso negado ao histórico de auditoria.')

        ativo = get_object_or_404(Ativo, pk=pk)
        filtros = _get_auditoria_filters_from_request(request)
        eventos = _build_asset_audit_timeline(
            ativo,
            actor_id=filtros['actor_id'],
            start_date=filtros['start_date'],
            end_date=filtros['end_date'],
        )

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="ativo-{ativo.numero_tombamento}-auditoria.csv"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Data/Hora', 'Usuário', 'Origem', 'Ação', 'Campo', 'Antes', 'Depois'])
        for ev in eventos:
            writer.writerow([
                ev['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
                ev['actor'],
                ev['origem'],
                ev['acao'],
                ev['campo'],
                ev['antes'],
                ev['depois'],
            ])

        return response


class AtivoAuditExportPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if not _user_can_access_asset_audit(request.user):
            raise PermissionDenied('Acesso negado ao histórico de auditoria.')

        ativo = get_object_or_404(Ativo, pk=pk)
        filtros = _get_auditoria_filters_from_request(request)
        eventos = _build_asset_audit_timeline(
            ativo,
            actor_id=filtros['actor_id'],
            start_date=filtros['start_date'],
            end_date=filtros['end_date'],
        )

        lines = [
            (
                f"{ev['timestamp'].strftime('%d/%m/%Y %H:%M:%S')} | {ev['actor']} | "
                f"{ev['origem']} | {ev['acao']} | {ev['campo']} | "
                f"{ev['antes']} -> {ev['depois']}"
            )
            for ev in eventos
        ]
        pdf_bytes = _build_simple_pdf(
            lines=lines,
            title=f'Historico de Auditoria - Ativo {ativo.numero_tombamento}',
        )

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ativo-{ativo.numero_tombamento}-auditoria.pdf"'
        return response


class OpcõesPorEmpresaView(LoginRequiredMixin, View):
    """
    Retorna Locais, Centros de Custo e Responsáveis vinculados a uma Empresa
    específica em formato JSON para os selects dinâmicos do formulário.
    """
    def get(self, request, empresa_id):
        locais = LocalFisico.objects.filter(empresa_id=empresa_id, ativo=True)
        centros = CentroCusto.objects.filter(empresa_id=empresa_id, ativo=True)
        responsaveis = Responsavel.objects.filter(empresa_id=empresa_id, ativo=True)
        
        data = {
            'locais': [
                {'id': l.id, 'text': f"{l.edificio} - {l.sala} ({l.descricao})" if l.descricao else f"{l.edificio} - {l.sala}"}
                for l in locais
            ],
            'centros': [{'id': c.id, 'text': f"{c.codigo} - {c.nome}"} for c in centros],
            'responsaveis': [{'id': r.id, 'text': r.nome} for r in responsaveis],
        }
        return JsonResponse(data)


class AtivoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Edição de ativo existente."""

    model = Ativo
    form_class = AtivoForm
    template_name = 'patrimonio/ativo_form.html'
    success_url = reverse_lazy('patrimonio:ativo-list')
    success_message = 'Ativo atualizado com sucesso!'


class AtivoStatusUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ativo = get_object_or_404(Ativo, pk=pk)

        novo_status = request.POST.get('status', '').strip()
        if not services.usuario_pode_transicionar_status(request.user, ativo.status, novo_status):
            raise PermissionDenied('Você não possui permissão para alterar para este status.')

        motivo = request.POST.get('motivo', '').strip()
        justificativa = request.POST.get('justificativa', '').strip()

        try:
            services.alterar_status_ativo(
                ativo,
                novo_status,
                usuario=request.user,
                motivo=motivo,
                justificativa=justificativa,
            )
            messages.success(request, 'Status do ativo atualizado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar status: {e}')

        return redirect('patrimonio:ativo-detail', pk=pk)


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
# GALERIA DE IMAGENS DO ATIVO
# =============================================================================


class AtivoImagemCreateView(LoginRequiredMixin, View):
    """Upload de imagem (ou múltiplas imagens) para a galeria do ativo."""

    def post(self, request, pk):
        ativo = get_object_or_404(Ativo, pk=pk)
        files = request.FILES.getlist('imagem')
        if not files:
            messages.error(request, 'Nenhuma imagem selecionada.')
            return redirect('patrimonio:ativo-detail', pk=pk)

        descricao = request.POST.get('descricao', '')
        tipo = request.POST.get('tipo', AtivoImagem.TipoImagem.OUTRO)
        principal = request.POST.get('principal') == 'on'

        count = 0
        for f in files:
            img = AtivoImagem(
                ativo=ativo,
                imagem=f,
                descricao=descricao,
                tipo=tipo,
                principal=principal if count == 0 else False,
                registrado_por=request.user,
            )
            img.save()
            count += 1

        if count == 1:
            messages.success(request, 'Imagem adicionada com sucesso!')
        else:
            messages.success(request, f'{count} imagens adicionadas com sucesso!')
        return redirect('patrimonio:ativo-detail', pk=pk)


class AtivoImagemDeleteView(LoginRequiredMixin, View):
    """Exclusão de imagem da galeria."""

    def post(self, request, pk):
        img = get_object_or_404(AtivoImagem, pk=pk)
        ativo_pk = img.ativo.pk
        img.imagem.delete(save=False)
        img.delete()
        messages.success(request, 'Imagem removida com sucesso.')
        return redirect('patrimonio:ativo-detail', pk=ativo_pk)


class AtivoImagemTogglePrincipalView(LoginRequiredMixin, View):
    """Marcar/desmarcar imagem como principal."""

    def post(self, request, pk):
        img = get_object_or_404(AtivoImagem, pk=pk)
        img.principal = not img.principal
        img.save()  # auto-unmark lógica está no model.save()
        if img.principal:
            messages.success(request, 'Imagem definida como principal.')
        else:
            messages.info(request, 'Imagem desmarcada como principal.')
        return redirect('patrimonio:ativo-detail', pk=img.ativo.pk)


# =============================================================================
# CADASTROS AUXILIARES — CRUDs Simples
# =============================================================================


class CategoriaListView(LoginRequiredMixin, ListView):
    model = CategoriaContabil
    template_name = 'patrimonio/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def get_queryset(self):
        return (
            CategoriaContabil.objects.filter(ativo=True)
            .select_related('parent')
            .annotate(
                ativos_count=Count(
                    'ativos',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                    distinct=True,
                ),
                ativos_valor_total=Sum(
                    'ativos__valor_aquisicao',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Categorias Contábeis'
        ctx['create_url'] = reverse_lazy('patrimonio:categoria-create')
        ctx['detail_url_name'] = 'patrimonio:categoria-detail'
        ctx['update_url_name'] = 'patrimonio:categoria-update'

        user = self.request.user
        show_metrics = user.is_authenticated
        ctx['show_manager_metrics'] = show_metrics

        if show_metrics:
            ativos_totais = Ativo.objects.filter(ativo=True).exclude(status='BAIXADO')
            totals = ativos_totais.aggregate(
                total_qtd=Count('id'),
                total_valor=Sum('valor_aquisicao'),
            )
            total_qtd = totals.get('total_qtd') or 0
            total_valor = totals.get('total_valor') or Decimal('0.00')
            ctx['ativos_total_qtd'] = total_qtd
            ctx['ativos_total_valor'] = total_valor

            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')
                obj.ativos_pct_qtd = (qtd / total_qtd * 100) if total_qtd else 0
                obj.ativos_pct_valor = (valor / total_valor * 100) if total_valor else 0

            # Chart data collection
            chart_qtd = []
            chart_valor = []
            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')
                if qtd > 0:
                    chart_qtd.append({'label': str(obj), 'value': int(qtd)})
                if valor > 0:
                    chart_valor.append({'label': str(obj), 'value': float(valor)})
            ctx['chart_data_qtd'] = json.dumps(chart_qtd)
            ctx['chart_data_valor'] = json.dumps(chart_valor)
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


class CentroCustoListView(LoginRequiredMixin, FilterView):
    model = CentroCusto
    template_name = 'patrimonio/centro_custo_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    filterset_class = CentroCustoFilter

    def get_queryset(self):
        return (
            CentroCusto.objects.filter(ativo=True)
            .select_related('empresa')
            .annotate(
                ativos_count=Count(
                    'ativos',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                    distinct=True,
                ),
                ativos_valor_total=Sum(
                    'ativos__valor_aquisicao',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Centros de Custo'
        ctx['create_url'] = reverse_lazy('patrimonio:centrocusto-create')
        ctx['update_url_name'] = 'patrimonio:centrocusto-update'

        user = self.request.user
        show_metrics = user.is_authenticated
        ctx['show_manager_metrics'] = show_metrics

        if show_metrics:
            ativos_totais = Ativo.objects.filter(ativo=True).exclude(status='BAIXADO')
            totals = ativos_totais.aggregate(
                total_qtd=Count('id'),
                total_valor=Sum('valor_aquisicao'),
            )
            total_qtd = totals.get('total_qtd') or 0
            total_valor = totals.get('total_valor') or Decimal('0.00')
            ctx['ativos_total_qtd'] = total_qtd
            ctx['ativos_total_valor'] = total_valor

            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')
                obj.ativos_pct_qtd = (qtd / total_qtd * 100) if total_qtd else 0
                obj.ativos_pct_valor = (valor / total_valor * 100) if total_valor else 0

            # Chart data collection
            chart_qtd = []
            chart_valor = []
            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')
                if qtd > 0:
                    chart_qtd.append({'label': str(obj), 'value': int(qtd)})
                if valor > 0:
                    chart_valor.append({'label': str(obj), 'value': float(valor)})
            ctx['chart_data_qtd'] = json.dumps(chart_qtd)
            ctx['chart_data_valor'] = json.dumps(chart_valor)
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


class LocalFisicoListView(LoginRequiredMixin, FilterView):
    model = LocalFisico
    template_name = 'patrimonio/local_fisico_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    filterset_class = LocalFisicoFilter

    def get_queryset(self):
        return (
            LocalFisico.objects.filter(ativo=True)
            .select_related('empresa')
            .annotate(
                ativos_count=Count(
                    'ativos',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                    distinct=True,
                ),
                ativos_valor_total=Sum(
                    'ativos__valor_aquisicao',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Locais Físicos'
        ctx['create_url'] = reverse_lazy('patrimonio:localfisico-create')
        ctx['update_url_name'] = 'patrimonio:localfisico-update'

        user = self.request.user
        show_metrics = user.is_authenticated
        ctx['show_manager_metrics'] = show_metrics

        if show_metrics:
            ativos_totais = Ativo.objects.filter(ativo=True).exclude(status='BAIXADO')
            totals = ativos_totais.aggregate(
                total_qtd=Count('id'),
                total_valor=Sum('valor_aquisicao'),
            )
            total_qtd = totals.get('total_qtd') or 0
            total_valor = totals.get('total_valor') or Decimal('0.00')
            ctx['ativos_total_qtd'] = total_qtd
            ctx['ativos_total_valor'] = total_valor

            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')
                obj.ativos_pct_qtd = (qtd / total_qtd * 100) if total_qtd else 0
                obj.ativos_pct_valor = (valor / total_valor * 100) if total_valor else 0
            # Chart data
            chart_qtd = []
            chart_valor = []
            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')

                if qtd > 0:
                    chart_qtd.append({'label': str(obj), 'value': int(qtd)})
                if valor > 0:
                    chart_valor.append({'label': str(obj), 'value': float(valor)})

            ctx['chart_data_qtd'] = json.dumps(chart_qtd)
            ctx['chart_data_valor'] = json.dumps(chart_valor)
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


class ResponsavelListView(LoginRequiredMixin, FilterView):
    model = Responsavel
    template_name = 'patrimonio/responsavel_list.html'
    context_object_name = 'object_list'
    paginate_by = 20

    filterset_class = ResponsavelFilter

    def get_queryset(self):
        return (
            Responsavel.objects.filter(ativo=True)
            .select_related('empresa')
            .annotate(
                ativos_count=Count(
                    'ativos',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                    distinct=True,
                ),
                ativos_valor_total=Sum(
                    'ativos__valor_aquisicao',
                    filter=Q(ativos__ativo=True) & ~Q(ativos__status='BAIXADO'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Responsáveis'
        ctx['create_url'] = reverse_lazy('patrimonio:responsavel-create')
        ctx['update_url_name'] = 'patrimonio:responsavel-update'

        user = self.request.user
        show_metrics = user.is_authenticated
        ctx['show_manager_metrics'] = show_metrics

        if show_metrics:
            ativos_totais = Ativo.objects.filter(ativo=True).exclude(status='BAIXADO')
            totals = ativos_totais.aggregate(
                total_qtd=Count('id'),
                total_valor=Sum('valor_aquisicao'),
            )
            total_qtd = totals.get('total_qtd') or 0
            total_valor = totals.get('total_valor') or Decimal('0.00')
            ctx['ativos_total_qtd'] = total_qtd
            ctx['ativos_total_valor'] = total_valor

            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')
                obj.ativos_pct_qtd = (qtd / total_qtd * 100) if total_qtd else 0
                obj.ativos_pct_valor = (valor / total_valor * 100) if total_valor else 0
            # Responsavel Chart data collection
            chart_qtd = []
            chart_valor = []
            for obj in ctx.get('object_list', []):
                qtd = getattr(obj, 'ativos_count', 0) or 0
                valor = getattr(obj, 'ativos_valor_total', None)
                if valor is None:
                    valor = Decimal('0.00')
                if qtd > 0:
                    chart_qtd.append({'label': str(obj), 'value': int(qtd)})
                if valor > 0:
                    chart_valor.append({'label': str(obj), 'value': float(valor)})
            ctx['chart_data_qtd'] = json.dumps(chart_qtd)
            ctx['chart_data_valor'] = json.dumps(chart_valor)
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
            .select_related('responsavel', 'empresa')
            .order_by('-data_inicio')
        )


class InventarioCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Inventario
    form_class = InventarioForm
    template_name = 'patrimonio/inventario_form.html'
    success_url = reverse_lazy('patrimonio:inventario-list')
    success_message = 'Inventário criado com sucesso!'


class InventarioUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Inventario
    form_class = InventarioForm
    template_name = 'patrimonio/inventario_form.html'
    success_message = 'Inventário atualizado com sucesso!'

    def dispatch(self, request, *args, **kwargs):
        inv = self.get_object()
        if inv.status != Inventario.StatusInventario.ABERTO:
            messages.error(request, 'Só é possível editar inventários com status ABERTO.')
            return redirect('patrimonio:inventario-detail', pk=inv.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('patrimonio:inventario-detail', kwargs={'pk': self.object.pk})


class InventarioDetailView(LoginRequiredMixin, DetailView):
    model = Inventario
    template_name = 'patrimonio/inventario_detail.html'
    context_object_name = 'inventario'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inv = self.object
        itens = (
            inv.itens.select_related('ativo', 'confirmado_por')
            .prefetch_related(
                Prefetch(
                    'evidencias',
                    queryset=InventarioItemEvidencia.objects.select_related('criado_por').order_by('-criado_em'),
                    to_attr='evidencias_list',
                )
            )
            .order_by('ativo__numero_tombamento')
        )

        # Filtros
        item_filter = InventarioItemFilter(self.request.GET, queryset=itens)
        ctx['item_filter'] = item_filter
        ctx['itens'] = item_filter.qs

        
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
            item.confirmado_por = request.user
            item.confirmado_em = timezone.now()
            # Tentar manter estado de conservação do ativo se não foi informado
            if not item.estado_conservacao_encontrado:
                item.estado_conservacao_encontrado = item.ativo.estado_conservacao
            msg = 'Item marcado como LOCALIZADO.'
        else:
            item.presenca = 'NAO_LOCALIZADO'
            item.confirmado_por = None
            item.confirmado_em = None
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


class InventarioItemEvidenciaListView(LoginRequiredMixin, DetailView):
    model = InventarioItem
    template_name = 'patrimonio/inventario_item_evidencia_list.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        item = self.object
        ctx['evidencias'] = item.evidencias.select_related('criado_por').order_by('-criado_em')
        return ctx


class InventarioItemEvidenciaCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(InventarioItem, pk=pk)
        form = InventarioItemEvidenciaForm(request.POST, request.FILES)
        if form.is_valid():
            evidencia = form.save(commit=False)
            evidencia.item = item
            evidencia.tipo = InventarioItemEvidencia.Tipo.AVARIA
            evidencia.criado_por = request.user
            evidencia.save()
            messages.success(request, 'Evidência registrada com sucesso.')
        else:
            messages.error(request, 'Erro ao registrar evidência. Verifique os campos.')
        return redirect('patrimonio:inventario-detail', pk=item.inventario.pk)


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


# =============================================================================
# IMÓVEIS — CRUD
# =============================================================================


class ImovelListView(LoginRequiredMixin, FilterView):
    """Listagem de imóveis com filtros e paginação."""

    model = Imovel
    template_name = 'patrimonio/imovel_list.html'
    context_object_name = 'itens'
    paginate_by = 20
    filterset_class = ImovelFilter

    def get_queryset(self):
        return (
            Imovel.objects.filter(ativo=True)
            .select_related('categoria', 'centro_custo', 'local_fisico', 'responsavel')
            .prefetch_related('situacoes')
            .order_by('-criado_em')
        )


class ImovelCreateView(LoginRequiredMixin, SuccessMessageMixin, CloneAtivoMixin, CreateView):
    """Cadastro de novo imóvel."""

    model = Imovel
    form_class = ImovelForm
    template_name = 'patrimonio/imovel_form.html'
    success_url = reverse_lazy('patrimonio:imovel-list')
    success_message = 'Imóvel cadastrado com sucesso!'

    @transaction.atomic
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            logger.error('Erro ao criar imóvel: %s', e)
            messages.error(self.request, f'Erro ao criar imóvel: {e}')
            return self.form_invalid(form)


class ImovelDetailView(LoginRequiredMixin, DetailView):
    """Detalhes do imóvel com histórico de situações."""

    model = Imovel
    template_name = 'patrimonio/imovel_detail.html'
    context_object_name = 'imovel'

    def get_queryset(self):
        return Imovel.objects.select_related(
            'categoria', 'centro_custo', 'local_fisico', 'responsavel'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        imovel = self.object
        ctx['situacoes'] = imovel.situacoes.filter(ativo=True).order_by('-data_inicio')
        ctx['situacao_atual'] = imovel.situacao_atual
        ctx['situacao_form'] = SituacaoImovelForm()
        ctx['depreciacoes'] = imovel.depreciacoes.filter(
            cenario='FISCAL'
        ).order_by('-ano_referencia', '-mes_referencia')[:12]
        ctx['movimentacoes'] = imovel.movimentacoes.select_related(
            'local_origem', 'local_destino',
            'responsavel_anterior', 'responsavel_novo',
        ).order_by('-data_movimentacao')[:10]
        return ctx


class ImovelUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Edição de imóvel existente."""

    model = Imovel
    form_class = ImovelForm
    template_name = 'patrimonio/imovel_form.html'
    success_url = reverse_lazy('patrimonio:imovel-list')
    success_message = 'Imóvel atualizado com sucesso!'


class ImovelDeleteView(LoginRequiredMixin, DeleteView):
    """Exclusão (soft delete) de imóvel."""

    model = Imovel
    success_url = reverse_lazy('patrimonio:imovel-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(request, 'Imóvel removido com sucesso.')
        return redirect(self.success_url)


class SituacaoImovelCreateView(LoginRequiredMixin, View):
    """Registrar nova situação/ocorrência para um imóvel."""

    def post(self, request, pk):
        imovel = get_object_or_404(Imovel, pk=pk)
        form = SituacaoImovelForm(request.POST)
        if form.is_valid():
            situacao = form.save(commit=False)
            situacao.imovel = imovel
            situacao.registrado_por = request.user
            situacao.save()
            messages.success(request, 'Situação registrada com sucesso!')
        else:
            messages.error(request, 'Erro ao registrar situação. Verifique os campos.')
        return redirect('patrimonio:imovel-detail', pk=pk)


# =============================================================================
# VEÍCULOS — CRUD
# =============================================================================


class VeiculoListView(LoginRequiredMixin, FilterView):
    """Listagem de veículos com filtros e paginação."""

    model = Veiculo
    template_name = 'patrimonio/veiculo_list.html'
    context_object_name = 'itens'
    paginate_by = 20
    filterset_class = VeiculoFilter

    def get_queryset(self):
        return (
            Veiculo.objects.filter(ativo=True)
            .select_related('categoria', 'centro_custo', 'local_fisico', 'responsavel')
            .order_by('-criado_em')
        )


class VeiculoCreateView(LoginRequiredMixin, SuccessMessageMixin, CloneAtivoMixin, CreateView):
    """Cadastro de novo veículo."""

    model = Veiculo
    form_class = VeiculoForm
    template_name = 'patrimonio/veiculo_form.html'
    success_url = reverse_lazy('patrimonio:veiculo-list')
    success_message = 'Veículo cadastrado com sucesso!'

    @transaction.atomic
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            logger.error('Erro ao criar veículo: %s', e)
            messages.error(self.request, f'Erro ao criar veículo: {e}')
            return self.form_invalid(form)


class VeiculoDetailView(LoginRequiredMixin, DetailView):
    """Detalhes do veículo."""

    model = Veiculo
    template_name = 'patrimonio/veiculo_detail.html'
    context_object_name = 'veiculo'

    def get_queryset(self):
        return Veiculo.objects.select_related(
            'categoria', 'centro_custo', 'local_fisico', 'responsavel'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        veiculo = self.object
        ctx['depreciacoes'] = veiculo.depreciacoes.filter(
            cenario='FISCAL'
        ).order_by('-ano_referencia', '-mes_referencia')[:12]
        ctx['movimentacoes'] = veiculo.movimentacoes.select_related(
            'local_origem', 'local_destino',
            'responsavel_anterior', 'responsavel_novo',
        ).order_by('-data_movimentacao')[:10]
        return ctx


class VeiculoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Edição de veículo existente."""

    model = Veiculo
    form_class = VeiculoForm
    template_name = 'patrimonio/veiculo_form.html'
    success_url = reverse_lazy('patrimonio:veiculo-list')
    success_message = 'Veículo atualizado com sucesso!'


class VeiculoDeleteView(LoginRequiredMixin, DeleteView):
    """Exclusão (soft delete) de veículo."""

    model = Veiculo
    success_url = reverse_lazy('patrimonio:veiculo-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(request, 'Veículo removido com sucesso.')
        return redirect(self.success_url)

"""
Serviços de lógica de negócio do módulo Patrimônio.

Contém: cálculo de depreciação, controle de baixa, gestão de inventário,
e conclusão de movimentações.
"""

import logging
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    Ativo,
    AtivoStatusHistorico,
    DepreciacaoRegistro,
    Inventario,
    InventarioItem,
    MotivoBaixa,
    Movimentacao,
)

logger = logging.getLogger('apps.patrimonio')


PERM_SET_ASSET_MAINTENANCE = 'patrimonio.can_set_asset_maintenance'
PERM_RETURN_ASSET_TO_ACTIVE = 'patrimonio.can_return_asset_to_active'
PERM_PROCESS_ASSET_DISPOSAL = 'patrimonio.can_process_asset_disposal'


ALLOWED_STATUS_TRANSITIONS = {
    Ativo.Status.ATIVO: {
        Ativo.Status.EM_MANUTENCAO,
        Ativo.Status.EM_PROCESSO_BAIXA,
    },
    Ativo.Status.EM_MANUTENCAO: {
        Ativo.Status.ATIVO,
        Ativo.Status.EM_PROCESSO_BAIXA,
    },
    Ativo.Status.EM_PROCESSO_BAIXA: {
        Ativo.Status.ATIVO,
    },
    Ativo.Status.BAIXADO: set(),
}


STATUS_REASON_CHOICES = {
    Ativo.Status.EM_MANUTENCAO: [
        ('QUEBRA', 'Quebra/Falha'),
        ('AJUSTE', 'Ajuste técnico'),
        ('PREVENTIVA', 'Manutenção preventiva'),
        ('INSPECAO', 'Inspeção técnica'),
        ('OUTRO', 'Outro'),
    ],
    Ativo.Status.ATIVO: [
        ('MANUTENCAO_CONCLUIDA', 'Manutenção concluída'),
        ('AJUSTE_CONCLUIDO', 'Ajuste concluído'),
        ('LIBERACAO_TECNICA', 'Liberação técnica'),
        ('OUTRO', 'Outro'),
    ],
    Ativo.Status.EM_PROCESSO_BAIXA: [
        ('OBSOLESCENCIA', 'Obsolescência'),
        ('IRRECUPERAVEL', 'Irrecuperável'),
        ('DESUSO', 'Desuso'),
        ('EXTRAVIO', 'Extravio'),
        ('OUTRO', 'Outro'),
    ],
}


TRANSITION_REQUIRED_PERMISSION = {
    (Ativo.Status.ATIVO, Ativo.Status.EM_MANUTENCAO): PERM_SET_ASSET_MAINTENANCE,
    (Ativo.Status.EM_MANUTENCAO, Ativo.Status.ATIVO): PERM_RETURN_ASSET_TO_ACTIVE,
    (Ativo.Status.EM_PROCESSO_BAIXA, Ativo.Status.ATIVO): PERM_RETURN_ASSET_TO_ACTIVE,
    (Ativo.Status.ATIVO, Ativo.Status.EM_PROCESSO_BAIXA): PERM_PROCESS_ASSET_DISPOSAL,
    (Ativo.Status.EM_MANUTENCAO, Ativo.Status.EM_PROCESSO_BAIXA): PERM_PROCESS_ASSET_DISPOSAL,
}


def status_transicoes_permitidas(status_atual: str) -> list[str]:
    permitidos = ALLOWED_STATUS_TRANSITIONS.get(status_atual, set())
    return [status for status, _ in Ativo.Status.choices if status in permitidos]


def usuario_pode_transicionar_status(
    usuario,
    status_atual: str,
    status_destino: str,
) -> bool:
    permissao = TRANSITION_REQUIRED_PERMISSION.get((status_atual, status_destino))
    if permissao is None:
        return False
    return bool(usuario and usuario.is_authenticated and usuario.has_perm(permissao))


def status_transicoes_permitidas_para_usuario(status_atual: str, usuario) -> list[str]:
    return [
        status_destino
        for status_destino in status_transicoes_permitidas(status_atual)
        if usuario_pode_transicionar_status(usuario, status_atual, status_destino)
    ]


def status_motivos_disponiveis(status_destino: str) -> list[tuple[str, str]]:
    return STATUS_REASON_CHOICES.get(status_destino, [('OUTRO', 'Outro')])


def alterar_status_ativo(
    ativo: Ativo,
    novo_status: str,
    usuario=None,
    motivo: str = '',
    justificativa: str = '',
) -> Ativo:
    """Altera o status do ativo respeitando regras de transição.

    Observação:
    - A transição para BAIXADO deve ocorrer pelo fluxo de baixa
      (registrar_baixa), para manter trilha e justificativa.
    """
    if novo_status not in Ativo.Status.values:
        raise ValidationError('Status de destino inválido.')

    status_atual = ativo.status
    if novo_status == status_atual:
        raise ValidationError('O ativo já está neste status.')

    permitidos = ALLOWED_STATUS_TRANSITIONS.get(status_atual, set())
    if novo_status not in permitidos:
        raise ValidationError(
            f'Transição de status inválida: {status_atual} -> {novo_status}.'
        )

    motivo = (motivo or '').strip()
    justificativa = (justificativa or '').strip()
    if not motivo:
        raise ValidationError('Informe o motivo da alteração de status.')

    motivos_permitidos = {codigo for codigo, _ in status_motivos_disponiveis(novo_status)}
    if motivo not in motivos_permitidos:
        raise ValidationError('Motivo inválido para o status de destino.')

    if usuario is not None and not usuario_pode_transicionar_status(
        usuario,
        status_atual,
        novo_status,
    ):
        raise ValidationError('Usuário sem permissão para esta transição de status.')

    ativo.status = novo_status
    ativo.save(update_fields=['status', 'atualizado_em'])

    AtivoStatusHistorico.objects.create(
        ativo=ativo,
        status_anterior=status_atual,
        status_novo=novo_status,
        motivo=motivo,
        justificativa=justificativa,
        alterado_por=usuario if getattr(usuario, 'is_authenticated', False) else None,
    )

    return ativo


# =============================================================================
# DEPRECIAÇÃO
# =============================================================================


def calcular_depreciacao_mensal(
    ativo: Ativo,
    ano: int,
    mes: int,
    cenario: str = 'FISCAL',
) -> DepreciacaoRegistro | None:
    """
    Calcula e registra a depreciação de UM ativo para UM mês.

    Método: Linear (Cotas Constantes).
    Fórmula: (Valor Aquisição - Valor Residual) / Vida Útil (meses)

    Retorna None se o ativo não deve ser depreciado (guards):
    - Ativo não é depreciável
    - Ativo está baixado
    - Já existe registro para este mês/cenário
    - Valor contábil já atingiu o valor residual
    """
    # Guards
    if not ativo.depreciavel:
        return None
    if ativo.status == 'BAIXADO':
        return None

    # Verificar se já existe registro para este mês/cenário
    if DepreciacaoRegistro.objects.filter(
        ativo=ativo,
        ano_referencia=ano,
        mes_referencia=mes,
        cenario=cenario,
    ).exists():
        return None

    # Cálculos
    base_depreciavel = ativo.valor_aquisicao - ativo.valor_residual
    if base_depreciavel <= 0:
        return None

    cota_mensal = (base_depreciavel / ativo.vida_util_meses).quantize(
        Decimal('0.01')
    )

    # Depreciação acumulada anterior
    ultimo = (
        ativo.depreciacoes.filter(cenario=cenario)
        .order_by('-ano_referencia', '-mes_referencia')
        .first()
    )
    acumulada_anterior = (
        ultimo.depreciacao_acumulada if ultimo else Decimal('0.00')
    )

    # Verificar se já atingiu valor residual
    nbv_anterior = ativo.valor_aquisicao - acumulada_anterior
    if nbv_anterior <= ativo.valor_residual:
        return None

    # Ajustar última cota para não ultrapassar o residual
    if (acumulada_anterior + cota_mensal) > base_depreciavel:
        cota_mensal = base_depreciavel - acumulada_anterior

    if cota_mensal <= 0:
        return None

    nova_acumulada = acumulada_anterior + cota_mensal
    nbv = ativo.valor_aquisicao - nova_acumulada

    return DepreciacaoRegistro.objects.create(
        ativo=ativo,
        ano_referencia=ano,
        mes_referencia=mes,
        cenario=cenario,
        valor_depreciado_mes=cota_mensal,
        depreciacao_acumulada=nova_acumulada,
        valor_contabil_atual=nbv,
    )


def processar_depreciacao_lote(
    ano: int,
    mes: int,
    cenario: str = 'FISCAL',
) -> dict:
    """
    Processa depreciação para TODOS os ativos elegíveis em lote.
    Retorna estatísticas do processamento.
    """
    ativos = Ativo.objects.depreciaveis().select_related('categoria')

    processados = 0
    ignorados = 0
    erros: list[dict] = []

    for ativo in ativos.iterator():
        try:
            resultado = calcular_depreciacao_mensal(ativo, ano, mes, cenario)
            if resultado:
                processados += 1
            else:
                ignorados += 1
        except Exception as e:
            logger.error(
                'Erro ao depreciar ativo %s: %s',
                ativo.numero_tombamento,
                e,
            )
            erros.append({
                'ativo': ativo.numero_tombamento,
                'erro': str(e),
            })

    logger.info(
        'Depreciação %s/%s (%s): %d processados, %d ignorados, %d erros',
        mes,
        ano,
        cenario,
        processados,
        ignorados,
        len(erros),
    )

    return {
        'processados': processados,
        'ignorados': ignorados,
        'erros': erros,
        'total': processados + ignorados + len(erros),
    }


# =============================================================================
# BAIXA PATRIMONIAL
# =============================================================================


def registrar_baixa(
    ativo: Ativo,
    tipo: str,
    justificativa: str,
    autorizado_por,
) -> MotivoBaixa:
    """
    Registra a baixa de um ativo com validações.

    Regras:
    1. Ativo não pode já estar baixado
    2. Ativo não pode ter movimentações pendentes (SOLICITADA ou APROVADA)
    3. Ao baixar, o status muda para BAIXADO e a depreciação cessa
    """
    if not (
        autorizado_por
        and getattr(autorizado_por, 'is_authenticated', False)
        and autorizado_por.has_perm(PERM_PROCESS_ASSET_DISPOSAL)
    ):
        raise ValidationError('Usuário sem permissão para iniciar/processar baixa.')

    if ativo.status == 'BAIXADO':
        raise ValidationError('Ativo já está baixado.')

    # Verificar movimentações pendentes
    movimentacoes_pendentes = ativo.movimentacoes.filter(
        status__in=['SOLICITADA', 'APROVADA']
    ).exists()
    if movimentacoes_pendentes:
        raise ValidationError(
            'Não é possível baixar: ativo possui movimentações pendentes. '
            'Conclua ou cancele as movimentações antes de prosseguir.'
        )

    with transaction.atomic():
        # Registrar baixa
        baixa = MotivoBaixa.objects.create(
            ativo=ativo,
            tipo=tipo,
            data_baixa=date.today(),
            justificativa=justificativa,
            autorizado_por=autorizado_por,
            valor_contabil_baixa=ativo.valor_contabil_atual,
        )

        # Atualizar status do ativo
        ativo.status = 'BAIXADO'
        ativo.save(update_fields=['status', 'atualizado_em'])

        logger.info(
            'Ativo %s baixado. Tipo: %s. Valor contábil: %s',
            ativo.numero_tombamento,
            tipo,
            baixa.valor_contabil_baixa,
        )

        return baixa


# =============================================================================
# MOVIMENTAÇÃO
# =============================================================================


def aprovar_movimentacao(
    movimentacao: Movimentacao,
    aprovado_por,
) -> None:
    """Aprova uma movimentação solicitada."""
    if movimentacao.status != 'SOLICITADA':
        raise ValidationError('Somente movimentações solicitadas podem ser aprovadas.')

    movimentacao.status = 'APROVADA'
    movimentacao.aprovado_por = aprovado_por
    movimentacao.save(update_fields=['status', 'aprovado_por', 'atualizado_em'])

    logger.info(
        'Movimentação %d do ativo %s aprovada por %s',
        movimentacao.pk,
        movimentacao.ativo.numero_tombamento,
        aprovado_por,
    )


def concluir_movimentacao(movimentacao: Movimentacao) -> None:
    """
    Conclui uma movimentação aprovada, atualizando o ativo.

    Atualiza: local_fisico, responsavel, centro_custo do ativo.
    """
    if movimentacao.status != 'APROVADA':
        raise ValidationError(
            'Movimentação precisa estar aprovada para ser concluída.'
        )

    with transaction.atomic():
        ativo = movimentacao.ativo

        # Atualizar ativo com novos dados
        campos_para_atualizar = ['local_fisico', 'responsavel', 'atualizado_em']
        ativo.local_fisico = movimentacao.local_destino
        ativo.responsavel = movimentacao.responsavel_novo

        if movimentacao.centro_custo_destino:
            ativo.centro_custo = movimentacao.centro_custo_destino
            campos_para_atualizar.append('centro_custo')

        ativo.save(update_fields=campos_para_atualizar)

        movimentacao.status = 'CONCLUIDA'
        movimentacao.save(update_fields=['status', 'atualizado_em'])

        logger.info(
            'Movimentação %d do ativo %s concluída. '
            'Novo local: %s, Novo responsável: %s',
            movimentacao.pk,
            ativo.numero_tombamento,
            movimentacao.local_destino,
            movimentacao.responsavel_novo,
        )


def cancelar_movimentacao(movimentacao: Movimentacao) -> None:
    """Cancela uma movimentação."""
    if movimentacao.status in ['CONCLUIDA', 'CANCELADA']:
        raise ValidationError('Movimentação já finalizada, não pode ser cancelada.')

    movimentacao.status = 'CANCELADA'
    movimentacao.save(update_fields=['status', 'atualizado_em'])


# =============================================================================
# INVENTÁRIO
# =============================================================================


def gerar_snapshot_inventario(inventario: Inventario) -> int:
    """
    Gera a lista de corte (snapshot) com todos os ativos elegíveis.
    Cria InventarioItems com presenca='NAO_LOCALIZADO' para cada ativo.

    Retorna a quantidade de itens gerados.
    """
    if inventario.itens.exists():
        raise ValidationError(
            'Este inventário já possui itens. '
            'Exclua os itens existentes ou crie um novo inventário.'
        )

    ativos_elegiveis = Ativo.objects.filter(
        ativo=True,
        status__in=['ATIVO', 'EM_MANUTENCAO'],
    ).order_by('numero_tombamento')

    itens = [
        InventarioItem(
            inventario=inventario,
            ativo=ativo,
            presenca='NAO_LOCALIZADO',
        )
        for ativo in ativos_elegiveis
    ]

    InventarioItem.objects.bulk_create(itens)

    # Atualizar status para EM_ANDAMENTO
    inventario.status = 'EM_ANDAMENTO'
    inventario.save(update_fields=['status', 'atualizado_em'])

    logger.info(
        'Snapshot do inventário %s gerado: %d itens',
        inventario.codigo,
        len(itens),
    )

    return len(itens)


def finalizar_inventario(inventario: Inventario) -> dict:
    """
    Finaliza um inventário e retorna estatísticas.
    """
    if inventario.status != 'EM_ANDAMENTO':
        raise ValidationError('Somente inventários em andamento podem ser finalizados.')

    localizados = inventario.itens.filter(presenca='LOCALIZADO').count()
    nao_localizados = inventario.itens.filter(presenca='NAO_LOCALIZADO').count()
    sobras = inventario.sobras.count()
    total = inventario.itens.count()

    taxa_conformidade = (localizados / total * 100) if total > 0 else 0

    inventario.status = 'CONCLUIDO'
    inventario.data_fim = date.today()
    inventario.save(update_fields=['status', 'data_fim', 'atualizado_em'])

    logger.info(
        'Inventário %s finalizado. Localizados: %d, Não localizados: %d, '
        'Sobras: %d, Taxa: %.1f%%',
        inventario.codigo,
        localizados,
        nao_localizados,
        sobras,
        taxa_conformidade,
    )

    return {
        'localizados': localizados,
        'nao_localizados': nao_localizados,
        'sobras': sobras,
        'total': total,
        'taxa_conformidade': round(taxa_conformidade, 1),
    }

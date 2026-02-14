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
    DepreciacaoRegistro,
    Inventario,
    InventarioItem,
    MotivoBaixa,
    Movimentacao,
)

logger = logging.getLogger('apps.patrimonio')


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
        Ativo.objects.filter(pk=ativo.pk).update(
            status='BAIXADO',
        )

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
        campos_para_atualizar = ['local_fisico', 'responsavel']
        ativo.local_fisico = movimentacao.local_destino
        ativo.responsavel = movimentacao.responsavel_novo

        if movimentacao.centro_custo_destino:
            ativo.centro_custo = movimentacao.centro_custo_destino
            campos_para_atualizar.append('centro_custo')

        # Usar update direto para evitar full_clean (tombamento check)
        Ativo.objects.filter(pk=ativo.pk).update(
            local_fisico=movimentacao.local_destino,
            responsavel=movimentacao.responsavel_novo,
            **(
                {'centro_custo': movimentacao.centro_custo_destino}
                if movimentacao.centro_custo_destino
                else {}
            ),
        )

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

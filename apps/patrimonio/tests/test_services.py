"""
Testes unitários para o módulo Patrimônio: models e services.

Cobre: depreciação (linear, guards, lote), baixa, movimentação, inventário.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.patrimonio.models import (
    Ativo,
    CategoriaContabil,
    CentroCusto,
    DepreciacaoRegistro,
    Inventario,
    InventarioItem,
    LocalFisico,
    MotivoBaixa,
    Movimentacao,
    Responsavel,
)
from apps.patrimonio import services


class _TestDataMixin:
    """Mixin com setup de dados de teste reutilizáveis."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

        cls.categoria = CategoriaContabil.objects.create(
            codigo='CAT-TST',
            nome='Categoria Teste',
            taxa_depreciacao_anual=Decimal('20.00'),
            vida_util_padrao_meses=60,
        )

        cls.centro_custo = CentroCusto.objects.create(
            codigo='CC-TST',
            nome='Centro Teste',
            departamento='Teste',
        )

        cls.local = LocalFisico.objects.create(
            codigo='LOC-TST',
            edificio='Prédio Teste',
            andar='1º',
            sala='Sala 101',
        )

        cls.local_destino = LocalFisico.objects.create(
            codigo='LOC-DST',
            edificio='Prédio Destino',
            andar='2º',
            sala='Sala 201',
        )

        cls.responsavel = Responsavel.objects.create(
            matricula='TST001',
            nome='Responsável Teste',
            cargo='Testador',
        )

        cls.responsavel_novo = Responsavel.objects.create(
            matricula='TST002',
            nome='Novo Responsável',
            cargo='Testador 2',
        )

    def _criar_ativo(self, **kwargs):
        """Helper para criar ativo com defaults."""
        defaults = {
            'numero_tombamento': f'TOMB-TEST-{Ativo.objects.count() + 1:04d}',
            'descricao_detalhada': 'Ativo de teste',
            'categoria': self.categoria,
            'centro_custo': self.centro_custo,
            'local_fisico': self.local,
            'responsavel': self.responsavel,
            'data_aquisicao': date.today() - timedelta(days=365),
            'valor_aquisicao': Decimal('12000.00'),
            'valor_residual': Decimal('2000.00'),
            'vida_util_meses': 60,
        }
        defaults.update(kwargs)
        return Ativo.objects.create(**defaults)


# =============================================================================
# TESTES DOS MODELS
# =============================================================================


class TestAtivoModel(_TestDataMixin, TestCase):
    """Testes do model Ativo."""

    def test_criacao_ativo_valido(self):
        ativo = self._criar_ativo(numero_tombamento='TOMB-VALID')
        self.assertEqual(ativo.numero_tombamento, 'TOMB-VALID')
        self.assertEqual(ativo.status, 'ATIVO')
        self.assertEqual(ativo.estado_conservacao, 'NOVO')
        self.assertTrue(ativo.depreciavel)

    def test_tombamento_imutavel(self):
        """Tombamento não pode ser alterado após criação."""
        ativo = self._criar_ativo(numero_tombamento='TOMB-IMUT')
        ativo.numero_tombamento = 'TOMB-ALTERADO'
        with self.assertRaises(ValidationError) as ctx:
            ativo.save()
        self.assertIn('numero_tombamento', ctx.exception.message_dict)

    def test_tombamento_unico(self):
        """Dois ativos não podem ter o mesmo tombamento."""
        self._criar_ativo(numero_tombamento='TOMB-UNICO')
        with self.assertRaises(Exception):
            self._criar_ativo(numero_tombamento='TOMB-UNICO')

    def test_soft_delete(self):
        """Soft delete desativa sem remover."""
        ativo = self._criar_ativo()
        ativo.soft_delete()
        ativo.refresh_from_db()
        self.assertFalse(ativo.ativo)

    def test_queryset_ativos_operacionais(self):
        """QuerySet filtra ativos operacionais."""
        ativo1 = self._criar_ativo(numero_tombamento='TOMB-OP1')
        ativo2 = self._criar_ativo(numero_tombamento='TOMB-OP2')
        ativo2.soft_delete()
        ativo3 = self._criar_ativo(
            numero_tombamento='TOMB-OP3', status='BAIXADO'
        )

        operacionais = Ativo.objects.ativos_operacionais()
        self.assertIn(ativo1, operacionais)
        self.assertNotIn(ativo2, operacionais)
        self.assertNotIn(ativo3, operacionais)

    def test_queryset_depreciaveis(self):
        """QuerySet filtra apenas depreciáveis e ativos."""
        ativo_depr = self._criar_ativo(numero_tombamento='TOMB-D1')
        ativo_nao_depr = self._criar_ativo(
            numero_tombamento='TOMB-D2', depreciavel=False
        )
        ativo_baixado = self._criar_ativo(
            numero_tombamento='TOMB-D3', status='BAIXADO'
        )

        depreciaveis = Ativo.objects.depreciaveis()
        self.assertIn(ativo_depr, depreciaveis)
        self.assertNotIn(ativo_nao_depr, depreciaveis)
        self.assertNotIn(ativo_baixado, depreciaveis)

    def test_valor_contabil_sem_depreciacao(self):
        """Valor contábil igual a aquisição quando sem depreciação."""
        ativo = self._criar_ativo()
        self.assertEqual(ativo.valor_contabil_atual, Decimal('12000.00'))

    def test_depreciacao_acumulada_zero(self):
        """Depreciação acumulada zero quando sem registros."""
        ativo = self._criar_ativo()
        self.assertEqual(ativo.depreciacao_acumulada_total, Decimal('0.00'))

    def test_percentual_depreciado_zero(self):
        """Percentual zero quando sem depreciação."""
        ativo = self._criar_ativo()
        self.assertEqual(ativo.percentual_depreciado, Decimal('0.00'))


# =============================================================================
# TESTES DO SERVICE DE DEPRECIAÇÃO
# =============================================================================


class TestDepreciacaoService(_TestDataMixin, TestCase):
    """Testes do cálculo de depreciação."""

    def test_calculo_mensal_basico(self):
        """
        Valor: 12000, Residual: 2000, Vida: 60 meses
        Base depreciável: 10000
        Cota mensal: 10000 / 60 = 166.67
        """
        ativo = self._criar_ativo()
        registro = services.calcular_depreciacao_mensal(ativo, 2026, 1)

        self.assertIsNotNone(registro)
        self.assertEqual(registro.valor_depreciado_mes, Decimal('166.67'))
        self.assertEqual(registro.depreciacao_acumulada, Decimal('166.67'))
        self.assertEqual(
            registro.valor_contabil_atual,
            Decimal('12000.00') - Decimal('166.67'),
        )

    def test_depreciacao_acumulada_dois_meses(self):
        """Acumulação correta após dois meses."""
        ativo = self._criar_ativo()
        services.calcular_depreciacao_mensal(ativo, 2026, 1)
        reg2 = services.calcular_depreciacao_mensal(ativo, 2026, 2)

        expected_acum = Decimal('166.67') * 2
        self.assertEqual(reg2.depreciacao_acumulada, expected_acum)

    def test_guard_nao_depreciavel(self):
        """Ativo com depreciavel=False não deve ser depreciado."""
        ativo = self._criar_ativo(
            numero_tombamento='TOMB-ND', depreciavel=False
        )
        resultado = services.calcular_depreciacao_mensal(ativo, 2026, 1)
        self.assertIsNone(resultado)

    def test_guard_ativo_baixado(self):
        """Ativo baixado não deve ser depreciado."""
        ativo = self._criar_ativo(
            numero_tombamento='TOMB-BAX', status='BAIXADO'
        )
        resultado = services.calcular_depreciacao_mensal(ativo, 2026, 1)
        self.assertIsNone(resultado)

    def test_guard_duplicata_mesmo_mes(self):
        """Não cria registro duplicado para o mesmo mês/cenário."""
        ativo = self._criar_ativo()
        reg1 = services.calcular_depreciacao_mensal(ativo, 2026, 1)
        reg2 = services.calcular_depreciacao_mensal(ativo, 2026, 1)

        self.assertIsNotNone(reg1)
        self.assertIsNone(reg2)
        self.assertEqual(
            DepreciacaoRegistro.objects.filter(ativo=ativo).count(), 1
        )

    def test_guard_valor_residual_atingido(self):
        """Para quando valor contábil atinge o residual."""
        ativo = self._criar_ativo(
            numero_tombamento='TOMB-RES',
            valor_aquisicao=Decimal('1000.00'),
            valor_residual=Decimal('800.00'),
            vida_util_meses=60,
        )
        # Base depreciável: 200, cota: 200/60 = 3.33
        # Após ~60 meses deveria parar
        for mes in range(1, 70):
            ano = 2020 + (mes - 1) // 12
            m = ((mes - 1) % 12) + 1
            services.calcular_depreciacao_mensal(ativo, ano, m)

        total_depr = DepreciacaoRegistro.objects.filter(
            ativo=ativo, cenario='FISCAL'
        ).count()
        # Deve ter parado antes de 70 iterações
        self.assertLessEqual(total_depr, 61)

        # Verificar NBV >= residual
        ultimo = DepreciacaoRegistro.objects.filter(
            ativo=ativo, cenario='FISCAL'
        ).order_by('-ano_referencia', '-mes_referencia').first()
        self.assertGreaterEqual(ultimo.valor_contabil_atual, ativo.valor_residual)

    def test_processamento_lote(self):
        """Processar depreciação em lote para múltiplos ativos."""
        self._criar_ativo(numero_tombamento='TOMB-L1')
        self._criar_ativo(numero_tombamento='TOMB-L2')
        self._criar_ativo(
            numero_tombamento='TOMB-L3', depreciavel=False
        )

        resultado = services.processar_depreciacao_lote(2026, 1)

        self.assertEqual(resultado['processados'], 2)
        # Non-depreciable assets are excluded by depreciaveis() queryset
        self.assertEqual(resultado['ignorados'], 0)
        self.assertEqual(resultado['erros'], [])

    def test_cenarios_diferentes(self):
        """Fiscal e Societário são independentes."""
        ativo = self._criar_ativo(numero_tombamento='TOMB-CEN')

        reg_fiscal = services.calcular_depreciacao_mensal(
            ativo, 2026, 1, 'FISCAL'
        )
        reg_soc = services.calcular_depreciacao_mensal(
            ativo, 2026, 1, 'SOCIETARIO'
        )

        self.assertIsNotNone(reg_fiscal)
        self.assertIsNotNone(reg_soc)
        self.assertEqual(reg_fiscal.cenario, 'FISCAL')
        self.assertEqual(reg_soc.cenario, 'SOCIETARIO')

    def test_base_depreciavel_zero(self):
        """Aquisição == Residual → sem depreciação."""
        ativo = self._criar_ativo(
            numero_tombamento='TOMB-Z',
            valor_aquisicao=Decimal('1000.00'),
            valor_residual=Decimal('1000.00'),
        )
        resultado = services.calcular_depreciacao_mensal(ativo, 2026, 1)
        self.assertIsNone(resultado)


# =============================================================================
# TESTES DO SERVICE DE BAIXA
# =============================================================================


class TestBaixaService(_TestDataMixin, TestCase):
    """Testes do registro de baixa patrimonial."""

    def test_registrar_baixa_sucesso(self):
        """Baixa com sucesso atualiza status do ativo."""
        ativo = self._criar_ativo(numero_tombamento='TOMB-BX1')

        baixa = services.registrar_baixa(
            ativo=ativo,
            tipo='OBSOLESCENCIA',
            justificativa='Equipamento obsoleto',
            autorizado_por=self.user,
        )

        self.assertIsInstance(baixa, MotivoBaixa)
        self.assertEqual(baixa.tipo, 'OBSOLESCENCIA')

        # Ativo deve estar BAIXADO
        ativo.refresh_from_db()
        self.assertEqual(ativo.status, 'BAIXADO')

    def test_baixa_ativo_ja_baixado(self):
        """Não permite baixa de ativo já baixado."""
        ativo = self._criar_ativo(
            numero_tombamento='TOMB-BX2', status='BAIXADO'
        )
        with self.assertRaises(ValidationError):
            services.registrar_baixa(
                ativo, 'VENDA', 'Venda', self.user
            )

    def test_baixa_com_movimentacao_pendente(self):
        """Bloqueia baixa se há movimentação SOLICITADA."""
        ativo = self._criar_ativo(numero_tombamento='TOMB-BX3')
        Movimentacao.objects.create(
            ativo=ativo,
            local_origem=self.local,
            local_destino=self.local_destino,
            responsavel_anterior=self.responsavel,
            responsavel_novo=self.responsavel_novo,
            data_movimentacao=date.today(),
            motivo='Transferência',
            status='SOLICITADA',
        )

        with self.assertRaises(ValidationError):
            services.registrar_baixa(
                ativo, 'DOACAO', 'Doação', self.user
            )


# =============================================================================
# TESTES DO SERVICE DE MOVIMENTAÇÃO
# =============================================================================


class TestMovimentacaoService(_TestDataMixin, TestCase):
    """Testes do fluxo de movimentação."""

    def _criar_movimentacao(self, ativo, **kwargs):
        defaults = {
            'ativo': ativo,
            'local_origem': self.local,
            'local_destino': self.local_destino,
            'responsavel_anterior': self.responsavel,
            'responsavel_novo': self.responsavel_novo,
            'data_movimentacao': date.today(),
            'motivo': 'Transferência teste',
            'status': 'SOLICITADA',
        }
        defaults.update(kwargs)
        return Movimentacao.objects.create(**defaults)

    def test_aprovar_movimentacao(self):
        ativo = self._criar_ativo(numero_tombamento='TOMB-MV1')
        mov = self._criar_movimentacao(ativo)

        services.aprovar_movimentacao(mov, self.user)
        mov.refresh_from_db()

        self.assertEqual(mov.status, 'APROVADA')
        self.assertEqual(mov.aprovado_por, self.user)

    def test_concluir_movimentacao_atualiza_ativo(self):
        """Conclusão atualiza local e responsável do ativo."""
        ativo = self._criar_ativo(numero_tombamento='TOMB-MV2')
        mov = self._criar_movimentacao(ativo, status='APROVADA')

        services.concluir_movimentacao(mov)
        ativo.refresh_from_db()
        mov.refresh_from_db()

        self.assertEqual(mov.status, 'CONCLUIDA')
        self.assertEqual(ativo.local_fisico, self.local_destino)
        self.assertEqual(ativo.responsavel, self.responsavel_novo)

    def test_aprovar_nao_solicitada(self):
        """Só aceita aprovar movimentações SOLICITADAS."""
        ativo = self._criar_ativo(numero_tombamento='TOMB-MV3')
        mov = self._criar_movimentacao(ativo, status='CONCLUIDA')

        with self.assertRaises(ValidationError):
            services.aprovar_movimentacao(mov, self.user)

    def test_cancelar_movimentacao(self):
        ativo = self._criar_ativo(numero_tombamento='TOMB-MV4')
        mov = self._criar_movimentacao(ativo)

        services.cancelar_movimentacao(mov)
        mov.refresh_from_db()

        self.assertEqual(mov.status, 'CANCELADA')

    def test_cancelar_concluida_invalido(self):
        """Não cancela movimentação concluída."""
        ativo = self._criar_ativo(numero_tombamento='TOMB-MV5')
        mov = self._criar_movimentacao(ativo, status='CONCLUIDA')

        with self.assertRaises(ValidationError):
            services.cancelar_movimentacao(mov)


# =============================================================================
# TESTES DO SERVICE DE INVENTÁRIO
# =============================================================================


class TestInventarioService(_TestDataMixin, TestCase):
    """Testes de gerar snapshot e finalizar inventário."""

    def _criar_inventario(self, **kwargs):
        defaults = {
            'codigo': f'INV-TST-{Inventario.objects.count() + 1:03d}',
            'data_inicio': date.today(),
            'responsavel': self.responsavel,
        }
        defaults.update(kwargs)
        return Inventario.objects.create(**defaults)

    def test_gerar_snapshot(self):
        """Snapshot cria itens para todos os ativos elegíveis."""
        a1 = self._criar_ativo(numero_tombamento='TOMB-IV1')
        a2 = self._criar_ativo(numero_tombamento='TOMB-IV2')
        # Baixado não entra
        self._criar_ativo(numero_tombamento='TOMB-IV3', status='BAIXADO')

        inv = self._criar_inventario()
        total = services.gerar_snapshot_inventario(inv)

        self.assertEqual(total, 2)
        self.assertEqual(inv.itens.count(), 2)
        # Todos iniciam como NAO_LOCALIZADO
        self.assertTrue(
            inv.itens.filter(presenca='NAO_LOCALIZADO').count() == 2
        )

    def test_snapshot_duplicado_bloqueado(self):
        """Não gera snapshot se já existem itens."""
        self._criar_ativo(numero_tombamento='TOMB-IV4')
        inv = self._criar_inventario()
        services.gerar_snapshot_inventario(inv)

        with self.assertRaises(ValidationError):
            services.gerar_snapshot_inventario(inv)

    def test_finalizar_inventario(self):
        """Finalizar atualiza status e calcula métricas."""
        self._criar_ativo(numero_tombamento='TOMB-IV5')
        self._criar_ativo(numero_tombamento='TOMB-IV6')

        inv = self._criar_inventario()
        services.gerar_snapshot_inventario(inv)

        # Marcar um como localizado
        item = inv.itens.first()
        item.presenca = 'LOCALIZADO'
        item.save()

        resultado = services.finalizar_inventario(inv)

        self.assertEqual(resultado['localizados'], 1)
        self.assertEqual(resultado['nao_localizados'], 1)
        self.assertEqual(resultado['total'], 2)
        self.assertEqual(resultado['taxa_conformidade'], 50.0)

        inv.refresh_from_db()
        self.assertEqual(inv.status, 'CONCLUIDO')
        self.assertIsNotNone(inv.data_fim)

    def test_finalizar_inventario_concluido(self):
        """Não finaliza inventário já concluído."""
        inv = self._criar_inventario(status='CONCLUIDO')
        with self.assertRaises(ValidationError):
            services.finalizar_inventario(inv)

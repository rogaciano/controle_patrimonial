"""
Management command para popular dados de teste.

Uso:
    python manage.py popular_dados_teste
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.patrimonio.models import (
    Ativo,
    CategoriaContabil,
    CentroCusto,
    LocalFisico,
    Responsavel,
)


class Command(BaseCommand):
    help = 'Popula o banco com dados de teste para desenvolvimento.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Populando dados de teste...'))

        # --- Categorias Contábeis ---
        categorias_data = [
            {'codigo': 'CAT-MOV', 'nome': 'Móveis e Utensílios', 'taxa': Decimal('10.00'), 'vida': 120},
            {'codigo': 'CAT-TI', 'nome': 'Equipamentos de TI', 'taxa': Decimal('20.00'), 'vida': 60},
            {'codigo': 'CAT-VEI', 'nome': 'Veículos', 'taxa': Decimal('20.00'), 'vida': 60},
            {'codigo': 'CAT-MAQ', 'nome': 'Máquinas e Equipamentos', 'taxa': Decimal('10.00'), 'vida': 120},
            {'codigo': 'CAT-IMO', 'nome': 'Imóveis / Edificações', 'taxa': Decimal('4.00'), 'vida': 300},
            {'codigo': 'CAT-TER', 'nome': 'Terrenos', 'taxa': Decimal('0.00'), 'vida': 0},
            {'codigo': 'CAT-FER', 'nome': 'Ferramentas', 'taxa': Decimal('10.00'), 'vida': 120},
        ]
        categorias = {}
        for c in categorias_data:
            obj, created = CategoriaContabil.objects.get_or_create(
                codigo=c['codigo'],
                defaults={
                    'nome': c['nome'],
                    'taxa_depreciacao_anual': c['taxa'],
                    'vida_util_padrao_meses': c['vida'],
                },
            )
            categorias[c['codigo']] = obj
            status = 'CRIADA' if created else 'já existe'
            self.stdout.write(f'  Categoria {c["codigo"]}: {status}')

        # Sub-categorias de TI
        for sub in [
            {'codigo': 'CAT-TI-NOTE', 'nome': 'Notebooks', 'taxa': Decimal('20.00'), 'vida': 60},
            {'codigo': 'CAT-TI-DESK', 'nome': 'Desktops', 'taxa': Decimal('20.00'), 'vida': 60},
            {'codigo': 'CAT-TI-IMP', 'nome': 'Impressoras', 'taxa': Decimal('20.00'), 'vida': 60},
            {'codigo': 'CAT-TI-SRV', 'nome': 'Servidores', 'taxa': Decimal('20.00'), 'vida': 60},
        ]:
            obj, created = CategoriaContabil.objects.get_or_create(
                codigo=sub['codigo'],
                defaults={
                    'nome': sub['nome'],
                    'taxa_depreciacao_anual': sub['taxa'],
                    'vida_util_padrao_meses': sub['vida'],
                    'parent': categorias['CAT-TI'],
                },
            )
            categorias[sub['codigo']] = obj

        # --- Centros de Custo ---
        centros_data = [
            {'codigo': 'CC-ADM', 'nome': 'Administração', 'depto': 'Administrativo', 'unidade': 'Sede'},
            {'codigo': 'CC-FIN', 'nome': 'Financeiro', 'depto': 'Financeiro', 'unidade': 'Sede'},
            {'codigo': 'CC-TI', 'nome': 'Tecnologia da Informação', 'depto': 'TI', 'unidade': 'Sede'},
            {'codigo': 'CC-RH', 'nome': 'Recursos Humanos', 'depto': 'RH', 'unidade': 'Sede'},
            {'codigo': 'CC-COM', 'nome': 'Comercial', 'depto': 'Vendas', 'unidade': 'Sede'},
            {'codigo': 'CC-OPR', 'nome': 'Operações', 'depto': 'Operacional', 'unidade': 'Filial 1'},
            {'codigo': 'CC-JUR', 'nome': 'Jurídico', 'depto': 'Jurídico', 'unidade': 'Sede'},
        ]
        centros = {}
        for c in centros_data:
            obj, _ = CentroCusto.objects.get_or_create(
                codigo=c['codigo'],
                defaults={'nome': c['nome'], 'departamento': c['depto'], 'unidade': c['unidade']},
            )
            centros[c['codigo']] = obj

        # --- Locais Físicos ---
        locais_data = [
            {'codigo': 'SEDE-T-RECEPCAO', 'edificio': 'Sede Principal', 'andar': 'Térreo', 'sala': 'Recepção'},
            {'codigo': 'SEDE-1-ADM', 'edificio': 'Sede Principal', 'andar': '1º Andar', 'sala': 'Sala Administrativa'},
            {'codigo': 'SEDE-1-FIN', 'edificio': 'Sede Principal', 'andar': '1º Andar', 'sala': 'Sala Financeiro'},
            {'codigo': 'SEDE-2-TI', 'edificio': 'Sede Principal', 'andar': '2º Andar', 'sala': 'Sala TI'},
            {'codigo': 'SEDE-2-RH', 'edificio': 'Sede Principal', 'andar': '2º Andar', 'sala': 'Sala RH'},
            {'codigo': 'SEDE-2-REUNIAO', 'edificio': 'Sede Principal', 'andar': '2º Andar', 'sala': 'Sala de Reunião A'},
            {'codigo': 'SEDE-3-DIR', 'edificio': 'Sede Principal', 'andar': '3º Andar', 'sala': 'Diretoria'},
            {'codigo': 'FIL1-T-OPR', 'edificio': 'Filial 1', 'andar': 'Térreo', 'sala': 'Operações'},
            {'codigo': 'DEP-GERAL', 'edificio': 'Depósito Central', 'andar': '', 'sala': 'Galpão'},
        ]
        locais = {}
        for l in locais_data:
            obj, _ = LocalFisico.objects.get_or_create(
                codigo=l['codigo'],
                defaults={'edificio': l['edificio'], 'andar': l['andar'], 'sala': l['sala']},
            )
            locais[l['codigo']] = obj

        # --- Responsáveis ---
        responsaveis_data = [
            {'matricula': 'MAT001', 'nome': 'Carlos Alberto Silva', 'cargo': 'Diretor Administrativo', 'email': 'carlos@empresa.com'},
            {'matricula': 'MAT002', 'nome': 'Maria Fernanda Santos', 'cargo': 'Coordenadora de TI', 'email': 'maria@empresa.com'},
            {'matricula': 'MAT003', 'nome': 'José Ricardo Oliveira', 'cargo': 'Gerente Financeiro', 'email': 'jose@empresa.com'},
            {'matricula': 'MAT004', 'nome': 'Ana Paula Costa', 'cargo': 'Analista de RH', 'email': 'ana@empresa.com'},
            {'matricula': 'MAT005', 'nome': 'Pedro Henrique Lima', 'cargo': 'Coordenador Comercial', 'email': 'pedro@empresa.com'},
            {'matricula': 'MAT006', 'nome': 'Lucas Ferreira Souza', 'cargo': 'Supervisor de Operações', 'email': 'lucas@empresa.com'},
        ]
        responsaveis = {}
        for r in responsaveis_data:
            obj, _ = Responsavel.objects.get_or_create(
                matricula=r['matricula'],
                defaults={'nome': r['nome'], 'cargo': r['cargo'], 'email': r['email']},
            )
            responsaveis[r['matricula']] = obj

        # --- Ativos ---
        hoje = date.today()
        ativos_data = [
            # Móveis
            {'tomb': 'TOMB00001', 'desc': 'Mesa de escritório em L - 1,60m x 1,20m', 'cat': 'CAT-MOV', 'cc': 'CC-ADM', 'local': 'SEDE-1-ADM', 'resp': 'MAT001', 'val': Decimal('1500.00'), 'res': Decimal('150.00'), 'vida': 120, 'data': hoje - timedelta(days=730)},
            {'tomb': 'TOMB00002', 'desc': 'Cadeira giratória presidente - couro sintético', 'cat': 'CAT-MOV', 'cc': 'CC-ADM', 'local': 'SEDE-3-DIR', 'resp': 'MAT001', 'val': Decimal('2200.00'), 'res': Decimal('200.00'), 'vida': 120, 'data': hoje - timedelta(days=730)},
            {'tomb': 'TOMB00003', 'desc': 'Armário alto 2 portas - MDF', 'cat': 'CAT-MOV', 'cc': 'CC-FIN', 'local': 'SEDE-1-FIN', 'resp': 'MAT003', 'val': Decimal('850.00'), 'res': Decimal('85.00'), 'vida': 120, 'data': hoje - timedelta(days=365)},
            {'tomb': 'TOMB00004', 'desc': 'Estante metálica 5 prateleiras', 'cat': 'CAT-MOV', 'cc': 'CC-FIN', 'local': 'SEDE-1-FIN', 'resp': 'MAT003', 'val': Decimal('420.00'), 'res': Decimal('42.00'), 'vida': 120, 'data': hoje - timedelta(days=365)},
            # TI
            {'tomb': 'TOMB00005', 'desc': 'Notebook Dell Latitude 5540 - i7 16GB 512SSD', 'cat': 'CAT-TI-NOTE', 'cc': 'CC-TI', 'local': 'SEDE-2-TI', 'resp': 'MAT002', 'val': Decimal('6500.00'), 'res': Decimal('650.00'), 'vida': 60, 'data': hoje - timedelta(days=547)},
            {'tomb': 'TOMB00006', 'desc': 'Notebook Lenovo ThinkPad T14 - i5 8GB 256SSD', 'cat': 'CAT-TI-NOTE', 'cc': 'CC-COM', 'local': 'SEDE-1-ADM', 'resp': 'MAT005', 'val': Decimal('4800.00'), 'res': Decimal('480.00'), 'vida': 60, 'data': hoje - timedelta(days=365)},
            {'tomb': 'TOMB00007', 'desc': 'Desktop HP ProDesk 400 G7 - i5 16GB 1TB', 'cat': 'CAT-TI-DESK', 'cc': 'CC-FIN', 'local': 'SEDE-1-FIN', 'resp': 'MAT003', 'val': Decimal('3200.00'), 'res': Decimal('320.00'), 'vida': 60, 'data': hoje - timedelta(days=730)},
            {'tomb': 'TOMB00008', 'desc': 'Monitor Dell 24" Full HD - P2422H', 'cat': 'CAT-TI', 'cc': 'CC-TI', 'local': 'SEDE-2-TI', 'resp': 'MAT002', 'val': Decimal('1200.00'), 'res': Decimal('120.00'), 'vida': 60, 'data': hoje - timedelta(days=547)},
            {'tomb': 'TOMB00009', 'desc': 'Impressora HP LaserJet Pro M404dn', 'cat': 'CAT-TI-IMP', 'cc': 'CC-ADM', 'local': 'SEDE-1-ADM', 'resp': 'MAT001', 'val': Decimal('2100.00'), 'res': Decimal('210.00'), 'vida': 60, 'data': hoje - timedelta(days=365)},
            {'tomb': 'TOMB00010', 'desc': 'Servidor Dell PowerEdge T340 - Xeon 32GB 2TB', 'cat': 'CAT-TI-SRV', 'cc': 'CC-TI', 'local': 'SEDE-2-TI', 'resp': 'MAT002', 'val': Decimal('18000.00'), 'res': Decimal('1800.00'), 'vida': 60, 'data': hoje - timedelta(days=1095)},
            # Veículos
            {'tomb': 'TOMB00011', 'desc': 'Fiat Strada Endurance 1.4 - Placa ABC1D23', 'cat': 'CAT-VEI', 'cc': 'CC-OPR', 'local': 'FIL1-T-OPR', 'resp': 'MAT006', 'val': Decimal('85000.00'), 'res': Decimal('25000.00'), 'vida': 60, 'data': hoje - timedelta(days=365)},
            {'tomb': 'TOMB00012', 'desc': 'VW Gol 1.0 - Placa DEF4G56', 'cat': 'CAT-VEI', 'cc': 'CC-COM', 'local': 'SEDE-T-RECEPCAO', 'resp': 'MAT005', 'val': Decimal('62000.00'), 'res': Decimal('18000.00'), 'vida': 60, 'data': hoje - timedelta(days=730)},
            # Máquinas e Equipamentos
            {'tomb': 'TOMB00013', 'desc': 'Ar condicionado Split 12000 BTUs - Elgin', 'cat': 'CAT-MAQ', 'cc': 'CC-TI', 'local': 'SEDE-2-TI', 'resp': 'MAT002', 'val': Decimal('2800.00'), 'res': Decimal('280.00'), 'vida': 120, 'data': hoje - timedelta(days=547)},
            {'tomb': 'TOMB00014', 'desc': 'Ar condicionado Split 18000 BTUs - Samsung', 'cat': 'CAT-MAQ', 'cc': 'CC-ADM', 'local': 'SEDE-1-ADM', 'resp': 'MAT001', 'val': Decimal('3500.00'), 'res': Decimal('350.00'), 'vida': 120, 'data': hoje - timedelta(days=365)},
            {'tomb': 'TOMB00015', 'desc': 'Projetor Epson PowerLite E20 - 3400 Lumens', 'cat': 'CAT-MAQ', 'cc': 'CC-ADM', 'local': 'SEDE-2-REUNIAO', 'resp': 'MAT001', 'val': Decimal('3200.00'), 'res': Decimal('320.00'), 'vida': 60, 'data': hoje - timedelta(days=730)},
            # Terreno (não depreciável)
            {'tomb': 'TOMB00016', 'desc': 'Terreno - Lote 15 Quadra B - Zona Industrial', 'cat': 'CAT-TER', 'cc': 'CC-ADM', 'local': 'DEP-GERAL', 'resp': 'MAT001', 'val': Decimal('350000.00'), 'res': Decimal('0.00'), 'vida': 0, 'data': hoje - timedelta(days=1825), 'depr': False},
            # Ferramentas
            {'tomb': 'TOMB00017', 'desc': 'Furadeira Bosch GSB 550 RE Professional', 'cat': 'CAT-FER', 'cc': 'CC-OPR', 'local': 'DEP-GERAL', 'resp': 'MAT006', 'val': Decimal('450.00'), 'res': Decimal('45.00'), 'vida': 120, 'data': hoje - timedelta(days=365)},
            {'tomb': 'TOMB00018', 'desc': 'Kit ferramentas manuais - Stanley 150pcs', 'cat': 'CAT-FER', 'cc': 'CC-OPR', 'local': 'FIL1-T-OPR', 'resp': 'MAT006', 'val': Decimal('680.00'), 'res': Decimal('68.00'), 'vida': 120, 'data': hoje - timedelta(days=365)},
            # Ativo em manutenção
            {'tomb': 'TOMB00019', 'desc': 'Notebook HP EliteBook 840 G9 - em reparo', 'cat': 'CAT-TI-NOTE', 'cc': 'CC-RH', 'local': 'SEDE-2-TI', 'resp': 'MAT004', 'val': Decimal('5200.00'), 'res': Decimal('520.00'), 'vida': 60, 'data': hoje - timedelta(days=547), 'status': 'EM_MANUTENCAO', 'estado': 'RUIM'},
            # Ativo antigo (totalmente depreciado)
            {'tomb': 'TOMB00020', 'desc': 'Impressora matricial Epson FX-2190 (antiga)', 'cat': 'CAT-TI-IMP', 'cc': 'CC-FIN', 'local': 'DEP-GERAL', 'resp': 'MAT003', 'val': Decimal('1800.00'), 'res': Decimal('180.00'), 'vida': 60, 'data': hoje - timedelta(days=2555), 'estado': 'INSERVIVEL'},
        ]

        created_count = 0
        for a in ativos_data:
            _, created = Ativo.objects.get_or_create(
                numero_tombamento=a['tomb'],
                defaults={
                    'descricao_detalhada': a['desc'],
                    'categoria': categorias[a['cat']],
                    'centro_custo': centros[a['cc']],
                    'local_fisico': locais[a['local']],
                    'responsavel': responsaveis[a['resp']],
                    'data_aquisicao': a['data'],
                    'valor_aquisicao': a['val'],
                    'valor_residual': a['res'],
                    'vida_util_meses': a['vida'],
                    'depreciavel': a.get('depr', True),
                    'status': a.get('status', 'ATIVO'),
                    'estado_conservacao': a.get('estado', 'BOM'),
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Dados de teste populados com sucesso!\n'
                f'  Categorias:    {len(categorias_data) + 4} (com subcategorias)\n'
                f'  Centros Custo: {len(centros_data)}\n'
                f'  Locais:        {len(locais_data)}\n'
                f'  Responsáveis:  {len(responsaveis_data)}\n'
                f'  Ativos:        {created_count} criados (de {len(ativos_data)} total)\n'
            )
        )

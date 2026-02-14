"""
Management command para processar depreciação mensal.

Uso:
    python manage.py processar_depreciacao
    python manage.py processar_depreciacao --ano=2026 --mes=2
    python manage.py processar_depreciacao --cenario=SOCIETARIO
    python manage.py processar_depreciacao --dry-run
"""

from datetime import date

from django.core.management.base import BaseCommand

from apps.patrimonio import services


class Command(BaseCommand):
    help = 'Processa a depreciação mensal de todos os ativos elegíveis.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ano',
            type=int,
            default=date.today().year,
            help='Ano de referência (default: ano atual)',
        )
        parser.add_argument(
            '--mes',
            type=int,
            default=date.today().month,
            help='Mês de referência (default: mês atual)',
        )
        parser.add_argument(
            '--cenario',
            type=str,
            default='FISCAL',
            choices=['FISCAL', 'SOCIETARIO'],
            help='Cenário de depreciação (default: FISCAL)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula o processamento sem gravar no banco',
        )

    def handle(self, *args, **options):
        ano = options['ano']
        mes = options['mes']
        cenario = options['cenario']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.NOTICE(
                f'Processando depreciação {mes:02d}/{ano} ({cenario})'
                f'{" [DRY RUN]" if dry_run else ""}...'
            )
        )

        if dry_run:
            from apps.patrimonio.models import Ativo
            total = Ativo.objects.depreciaveis().count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'[DRY RUN] {total} ativos seriam processados.'
                )
            )
            return

        resultado = services.processar_depreciacao_lote(ano, mes, cenario)

        self.stdout.write(
            self.style.SUCCESS(
                f'Depreciação concluída!\n'
                f'  Processados: {resultado["processados"]}\n'
                f'  Ignorados:   {resultado["ignorados"]}\n'
                f'  Erros:       {len(resultado["erros"])}\n'
                f'  Total:       {resultado["total"]}'
            )
        )

        if resultado['erros']:
            self.stdout.write(self.style.WARNING('Erros encontrados:'))
            for erro in resultado['erros']:
                self.stdout.write(
                    self.style.ERROR(
                        f'  - Ativo {erro["ativo"]}: {erro["erro"]}'
                    )
                )

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.db.models import Q

from apps.patrimonio.models import Ativo


class Command(BaseCommand):
    help = 'Atualiza o número de tombamento dos ativos para o padrão XXX-AA-999999.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra quantos registros seriam alterados, sem gravar no banco.',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regera tombamento de todos os ativos (inclusive os já no padrão).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limita a quantidade de registros processados (0 = sem limite).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_all = options['all']
        limit = options['limit']

        filtro_padrao = Q(numero_tombamento__regex=Ativo._TOMBAMENTO_REGEX)
        if force_all:
            qs = Ativo.objects.select_related('categoria').order_by('pk')
        else:
            qs = (
                Ativo.objects.select_related('categoria')
                .exclude(filtro_padrao)
                .order_by('pk')
            )

        if limit and limit > 0:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Nenhum ativo para atualizar.'))
            return

        proximo_seq = Ativo._proximo_sequencial_tombamento()

        self.stdout.write(
            self.style.NOTICE(
                f'Atualizando tombamentos ({total} registro(s))'
                f'{" [DRY RUN]" if dry_run else ""}...'
            )
        )

        if dry_run:
            amostra = list(qs[:10])
            for ativo in amostra:
                antigo = ativo.numero_tombamento
                novo = self._gerar_com_sequencial(ativo, proximo_seq)
                proximo_seq += 1
                self.stdout.write(f'- {ativo.pk}: {antigo} -> {novo}')
            if total > 10:
                self.stdout.write(f'... e mais {total - 10} registro(s).')
            return

        atualizados = 0
        erros = 0

        for ativo in qs.iterator(chunk_size=200):
            tentativas = 10
            last_error = None
            for _ in range(tentativas):
                novo = self._gerar_com_sequencial(ativo, proximo_seq)
                try:
                    with transaction.atomic():
                        Ativo.objects.filter(pk=ativo.pk).update(numero_tombamento=novo)
                    atualizados += 1
                    proximo_seq += 1
                    break
                except IntegrityError as e:
                    last_error = e
                    proximo_seq += 1
                    continue
            else:
                erros += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Falha ao atualizar ativo {ativo.pk} (atual: {ativo.numero_tombamento})'
                    )
                )
                if last_error:
                    self.stdout.write(self.style.ERROR(str(last_error)))

        self.stdout.write(
            self.style.SUCCESS(
                f'Concluído. Atualizados: {atualizados}. Erros: {erros}.'
            )
        )

    def _gerar_com_sequencial(self, ativo: Ativo, sequencial: int) -> str:
        codigo = (ativo.categoria.codigo or '').strip().upper()
        codigo = ''.join(ch for ch in codigo if ch.isalnum())
        if len(codigo) >= 3:
            prefixo = codigo[:3]
        else:
            prefixo = codigo.rjust(3, '0')
        ano = ativo.data_aquisicao.year % 100
        return f'{prefixo}-{ano:02d}-{sequencial:06d}'

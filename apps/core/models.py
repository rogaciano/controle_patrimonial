"""Modelos base do sistema - mixins e classes abstratas."""

from django.core.exceptions import ValidationError
from django.db import models


class BaseModel(models.Model):
    """Mixin base com campos de auditoria e soft delete."""

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        """Marca o registro como inativo (soft delete)."""
        self.ativo = False
        self.save(update_fields=['ativo', 'atualizado_em'])


class Empresa(BaseModel):
    """
    Representação de uma Empresa/Filial.
    Apenas uma (ou nenhuma) pode ser marcada como Matriz.
    """

    ESTADOS_CHOICES = (
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    )

    nome_razao = models.CharField('Razão Social', max_length=200)
    nome_fantasia = models.CharField('Nome Fantasia', max_length=150)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True, help_text='Formato: 00.000.000/0000-00')
    matriz = models.BooleanField('É Matriz?', default=False)
    cidade = models.CharField('Cidade', max_length=100)
    uf = models.CharField('UF', max_length=2, choices=ESTADOS_CHOICES)
    endereco = models.CharField('Endereço', max_length=250)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['-matriz', 'nome_fantasia']

    def __str__(self):
        return f"{self.nome_fantasia} ({self.cnpj})"

    def clean(self):
        super().clean()
        if self.matriz:
            # Verifica se já existe outra matriz
            qs = Empresa.objects.filter(matriz=True).exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'matriz': 'Já existe uma empresa definida como Matriz. Desmarque-a antes de definir esta como matriz.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

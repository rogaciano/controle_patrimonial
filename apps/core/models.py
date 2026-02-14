"""Modelos base do sistema - mixins e classes abstratas."""

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

"""Patrimonio app configuration."""

from django.apps import AppConfig


class PatrimonioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.patrimonio'
    verbose_name = 'Controle Patrimonial'

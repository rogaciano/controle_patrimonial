"""Validadores reutilizáveis do sistema."""

import re

from django.core.exceptions import ValidationError


def validar_cpf(value: str) -> None:
    """Valida CPF com dígitos verificadores."""
    cpf = re.sub(r'\D', '', value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if int(cpf[i]) != digito:
            raise ValidationError('CPF inválido.')


def validar_cnpj(value: str) -> None:
    """Valida CNPJ."""
    cnpj = re.sub(r'\D', '', value)
    if len(cnpj) != 14:
        raise ValidationError('CNPJ inválido.')


def validar_telefone(value: str) -> None:
    """Valida telefone (10-11 dígitos)."""
    telefone = re.sub(r'\D', '', value)
    if len(telefone) not in (10, 11):
        raise ValidationError('Telefone deve ter 10 ou 11 dígitos.')


def validar_cep(value: str) -> None:
    """Valida CEP (8 dígitos)."""
    cep = re.sub(r'\D', '', value)
    if len(cep) != 8:
        raise ValidationError('CEP deve ter 8 dígitos.')

from django import forms
from .models import Empresa

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nome_razao', 
            'nome_fantasia', 
            'cnpj', 
            'matriz', 
            'cidade', 
            'uf', 
            'endereco',
            'ativo'
        ]
        widgets = {
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'matriz': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

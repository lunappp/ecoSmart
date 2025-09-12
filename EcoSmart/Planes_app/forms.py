from django import forms
from .models import Plan, Suscripcion

class CrearPlanForm(forms.ModelForm):
    """
    Formulario para crear un nuevo plan.
    """
    class Meta:
        model = Plan
        fields = ['nombre', 'descripcion']

class UnirseAForm(forms.Form):
    """
    Formulario simple para unirse a un plan existente.
    """
    plan_id = forms.IntegerField(widget=forms.HiddenInput())
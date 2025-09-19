# Planes_app/forms.py

from django import forms
from .models import Plan, Suscripcion, Ingreso, Gasto

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
    
class IngresoForm(forms.ModelForm):
    class Meta:
        model = Ingreso
        fields = ['nombre', 'tipo_ingreso', 'cantidad']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600', 'placeholder': 'Nombre del ingreso'}),
            'tipo_ingreso': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600'}),
            'cantidad': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600', 'placeholder': 'Cantidad'}),
        }

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['nombre', 'tipo_gasto', 'cantidad']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600', 'placeholder': 'Nombre del gasto'}),
            'tipo_gasto': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600'}),
            'cantidad': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600', 'placeholder': 'Cantidad'}),
        }
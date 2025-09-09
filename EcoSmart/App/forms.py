from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Plan

class RegisterForm(UserCreationForm):
    
    username = forms.CharField(label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")
    firstName = forms.CharField(label="Primer nombre")
    lastName = forms.CharField(label="Apellido")
    password1 = forms.CharField(label="Contraseña")
    password2 = forms.CharField(label="Confirmar contraseña")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'firstName', 'lastName', 'password1', 'password2']


class PlanIndividualForm(forms.ModelForm):
    class Meta:
        model = Plan
        # Solo necesitamos que el usuario ingrese el nombre del plan
        fields = ['nombre']
        
    def save(self, user, commit=True):
        # Esta función personaliza el guardado.
        # Asigna el usuario actual y establece el tipo de plan como 'individual'.
        plan = super().save(commit=False)
        plan.usuario = user
        plan.tipo_plan = 'individual'
        if commit:
            plan.save()
        return plan
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Plan

class RegisterForm(UserCreationForm):
    
    username = forms.CharField(label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")
    password1 = forms.CharField(label="Contraseña")
    password2 = forms.CharField(label="Confirmar contraseña")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class PlanForm(forms.ModelForm):
    # Definimos las opciones para el tipo de plan
    TIPO_PLAN_CHOICES = [
        ('individual', 'Individual'),
        ('grupal', 'Grupal'),
    ]
    
    # Agregamos el campo para que el usuario lo elija
    tipo_plan = forms.ChoiceField(
        choices=TIPO_PLAN_CHOICES,
        widget=forms.RadioSelect, # Usamos radio buttons para una mejor UX
        initial='individual'
    )
    
    class Meta:
        model = Plan
        # Ahora incluimos el campo 'tipo_plan' en el formulario
        fields = ['nombre', 'tipo_plan']
        
    def save(self, user, commit=True):
        # Esta función personaliza el guardado.
        # Ya no necesitamos establecer el tipo_plan, ya que viene del formulario.
        plan = super().save(commit=False)
        plan.usuario = user
        if commit:
            plan.save()
        return plan
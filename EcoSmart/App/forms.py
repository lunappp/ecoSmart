from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

from .models import Plan, Profile

class RegisterForm(UserCreationForm):

    username = forms.CharField(label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")
    password1 = forms.CharField(label="Contraseña")
    password2 = forms.CharField(label="Confirmar contraseña")
    profile_picture = forms.ImageField(label="Foto de perfil", required=False)

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


class ProfileEditForm(forms.ModelForm):
    username = forms.CharField(label="Usuario", max_length=150, required=True)
    profile_picture = forms.ImageField(label="Foto de perfil", required=False)

    class Meta:
        model = User
        fields = ['username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['profile_picture'].initial = self.instance.profile.profile_picture

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            if self.cleaned_data.get('profile_picture'):
                profile.profile_picture = self.cleaned_data['profile_picture']
                profile.save()
        return user


class PasswordChangeFormCustom(PasswordChangeForm):
    old_password = forms.CharField(label="Contraseña actual", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirmar nueva contraseña", widget=forms.PasswordInput)
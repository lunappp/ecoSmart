from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

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

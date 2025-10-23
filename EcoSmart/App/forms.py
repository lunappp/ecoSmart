from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Profile, Plan

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

class ProfileEditForm(UserChangeForm):
    password = None
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['profile_picture'].initial = self.instance.profile.profile_picture

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, created = Profile.objects.get_or_create(user=user)
            if self.cleaned_data.get('profile_picture'):
                profile.profile_picture = self.cleaned_data['profile_picture']
                profile.save()
        return user

class PasswordChangeFormCustom(PasswordChangeForm):
    pass

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['nombre', 'tipo_plan']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ej: Viaje a Europa 2025'}),
            'tipo_plan': forms.Select(attrs={'class': 'form-select w-full rounded-lg border-gray-300 shadow-sm'}),
        }
        labels = {
            'nombre': 'Nombre del Plan',
            'tipo_plan': 'Tipo de Plan',
        }
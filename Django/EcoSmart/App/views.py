from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages


#------------------ Landing page ------------------#
#                        |                         #
#                        v                         #

def Landing(request):
    return render(request,'landing_page/index.html')

#---------------------- Auth ----------------------#
#                        |                         #
#                        v                         #

def Register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registro exitoso. ¡Bienvenido!")
            return redirect('Inicio')  # Redirige a la página principal
        messages.error(request, "Error en el registro. Verifique la información.")
    else:
        form = UserCreationForm()
    return render(request, 'auth/registro/registro.html', {'form': form})


def Login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"¡Hola, {username}! Has iniciado sesión con éxito.")
                return redirect('Inicio')  # Redirige a la página principal
            else:
                messages.error(request, "Usuario o contraseña inválidos.")
        else:
            messages.error(request, "Usuario o contraseña inválidos.")
    form = AuthenticationForm()
    return render(request, 'auth/login/login.html', {'form': form})

#----------------- menu principal -----------------#
#                        |                         #
#                        v                         #

def Inicio(request):
    return render(request, 'menu_principal/index.html')

def transacciones(request):
    return render(request, 'menu_principal/transacciones.html')

def Estadisticas(request):
    return render(request, 'menu_principal/Estadisticas.html')
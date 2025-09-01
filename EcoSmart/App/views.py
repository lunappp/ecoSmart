from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages

from App.forms import RegisterForm


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
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            register_form.save()
            return redirect('Inicio')
        else:
            errores = register_form.errors
        
            return render(request, 'auth/registro/registro.html', {
                'registerForm': register_form,
                'errores': errores
                
            })
    else:
        
        register_form = RegisterForm()
        return render(request, 'auth/registro/registro.html', {
            'registerForm': register_form
        })


def Login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("Inicio")  # O la página que quieras después de loguear
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            return render(request, "auth/login/login.html")

    return render(request, "auth/login/login.html")

#----------------- menu principal -----------------#
#                        |                         #
#                        v                         #

def Inicio(request):
    return render(request, 'menu_principal/index.html')

def transacciones(request):
    return render(request, 'menu_principal/transacciones.html')

def Estadisticas(request):
    return render(request, 'menu_principal/Estadisticas.html')
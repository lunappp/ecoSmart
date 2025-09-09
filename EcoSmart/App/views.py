from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages

from django.contrib.auth.decorators import login_required

from .forms import PlanIndividualForm
from .models import Plan

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
            return redirect("Dashboard")  # O la página que quieras después de loguear
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


#--------------------dashboard---------------------#
#                        |                         #
#                        v                         #

def Dashboard(request):
    return render(request, 'Dashboard/index.html')


def Dashboard_view(request):
    # Obtiene todos los planes (individuales y grupales) a los que pertenece el usuario actual.
    planes_del_usuario = Plan.objects.filter(usuario=request.user).order_by('-fecha_creacion')

    # Pasa la lista de planes a la plantilla HTML.
    return render(request, 'dashboard/index.html', {'planes_del_usuario': planes_del_usuario})


#--------------------- planes ---------------------#
#                        |                         #
#                        v                         #
def crear_plan_individual_view(request):
    if request.method == 'POST':
        form = PlanIndividualForm(request.POST)
        if form.is_valid():

            # El formulario se encarga de asignar el usuario y el tipo de plan.
            form.save(user=request.user)
            messages.success(request, "¡Tu plan individual se ha creado con éxito!")
            return redirect('Dashboard') # Redirige al dashboard
    else:
        form = PlanIndividualForm()
    
    return render(request, 'planes/crear_plan.html', {'form': form})
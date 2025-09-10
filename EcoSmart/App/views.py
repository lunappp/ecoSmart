from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages

from django.contrib.auth.decorators import login_required

from .forms import PlanForm
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
    """
    Vista que muestra el dashboard del usuario con sus planes.
    """
    # Filtra la base de datos para obtener todos los planes donde el usuario 
    # actual sea el creador. Esto obtiene los planes individuales.
    planes_del_usuario = Plan.objects.filter(usuario=request.user)

    # El siguiente paso (para planes grupales) requiere un modelo de membresía
    # o una relación ManyToManyField, lo cual ya discutimos. 
    # Si tienes esa tabla implementada, la lógica sería un poco más compleja
    # para incluir los planes grupales también. Por ahora, nos enfocamos en 
    # los planes individuales que ya creaste.

    # Pasa la lista de planes a la plantilla para que el bucle `{% for %}` los muestre.
    return render(request, 'dashboard/index.html', {'planes_del_usuario': planes_del_usuario})


#--------------------- planes ---------------------#
#                        |                         #
#                        v                         #
def crear_plan_view(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "¡Tu plan se ha creado con éxito!")
            return redirect('Dashboard')
    else:
        form = PlanForm()
    
    return render(request, 'planes/crear_plan.html', {'form': form})

def plan_individual(request):
    return render(request, 'planes/plan_individual.html')

def plan_grupal(request):
  return render(request, 'planes/plan_grupal.html')
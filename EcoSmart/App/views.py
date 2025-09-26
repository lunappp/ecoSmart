from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages

from django.contrib.auth.decorators import login_required


from Planes_app.models import Plan, Suscripcion # Asume estos modelos
from Planes_app.forms import CrearPlanForm, UnirseAForm # Asume estos formularios
from .forms import PlanForm
from .models import Plan

from App.forms import RegisterForm


#------------------ Landing page ------------------#
def Landing(request):
    return render(request,'landing_page/index.html')

#---------------------- Auth ----------------------#
def Register(request):
    if request.method == 'POST':
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            register_form.save()
            return redirect('Dashboard')
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
def Inicio(request):
    return render(request, 'menu_principal/index.html')
def transacciones(request):
    return render(request, 'menu_principal/transacciones.html')
def Estadisticas(request):
    return render(request, 'menu_principal/Estadisticas.html')

#--------------------Dashboard---------------------#
from Planes_app.models import Plan

def Dashboard(request):
    if not request.user.is_authenticated:
        return redirect('Login') 

    if request.method == 'POST' and 'crear_plan' in request.POST:
        crear_form = CrearPlanForm(request.POST)
        if crear_form.is_valid():
            nuevo_plan = crear_form.save(commit=False)
            nuevo_plan.creador = request.user
            # Obtener el tipo de plan desde el formulario y asignarlo
            tipo_plan = request.POST.get('tipo_plan')
            if tipo_plan in ['individual', 'grupal']:
                nuevo_plan.tipo_plan = tipo_plan
                nuevo_plan.save()
                Suscripcion.objects.create(usuario=request.user, plan=nuevo_plan)
                return redirect('Dashboard')

    elif request.method == 'POST' and 'unirse_a_plan' in request.POST:
        unirse_form = UnirseAForm(request.POST)
        if unirse_form.is_valid():
            plan_id = unirse_form.cleaned_data['plan_id']
            plan_a_unirse = Plan.objects.get(id=plan_id)
            Suscripcion.objects.create(usuario=request.user, plan=plan_a_unirse)
            return redirect('Dashboard')
    
    else:
        crear_form = CrearPlanForm()
        unirse_form = UnirseAForm()

    mis_planes = request.user.suscripciones.all()
    
    context = {
        'mis_planes': mis_planes,
        'crear_form': crear_form,
        'unirse_form': unirse_form
    }

    return render(request, 'dashboard/index.html', context)
#--------------------- planes ---------------------#
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
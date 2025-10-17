from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages

from django.contrib.auth.decorators import login_required


from Planes_app.models import Plan, Suscripcion, Invitacion # Asume estos modelos
from Planes_app.forms import CrearPlanForm # Asume estos formularios
from .forms import PlanForm, ProfileEditForm, PasswordChangeFormCustom
from .models import Plan, Profile

from App.forms import RegisterForm


#------------------ Landing page ------------------#
def Landing(request):
    return render(request,'landing_page/index.html')

#---------------------- Auth ----------------------#
def Register(request):
    if request.method == 'POST':
        register_form = RegisterForm(request.POST, request.FILES)
        if register_form.is_valid():
            user = register_form.save()
            profile_picture = register_form.cleaned_data.get('profile_picture')
            if profile_picture:
                Profile.objects.create(user=user, profile_picture=profile_picture)
            else:
                Profile.objects.create(user=user)
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

    else:
        crear_form = CrearPlanForm()

    mis_planes = request.user.suscripciones.all()
    invitaciones_pendientes = Invitacion.objects.filter(invitado=request.user, estado='pendiente')

    context = {
        'mis_planes': mis_planes,
        'crear_form': crear_form,
        'invitaciones_pendientes': invitaciones_pendientes
    }

    return render(request, 'dashboard/index.html', context)
#--------------------- planes ---------------------#
def crear_plan_view(request):
    if request.method == 'POST':
        form = CrearPlanForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo_plan = form.save(commit=False)
            nuevo_plan.creador = request.user
            nuevo_plan.save()
            Suscripcion.objects.create(usuario=request.user, plan=nuevo_plan)
            messages.success(request, "¡Tu plan se ha creado con éxito!")
            return redirect('Dashboard')
    else:
        form = CrearPlanForm()

    return render(request, 'planes/crear_plan.html', {'form': form})

def plan_individual(request):
    return render(request, 'planes/plan_individual.html')

def plan_grupal(request):
  return render(request, 'planes/plan_grupal.html')

@login_required
def aceptar_invitacion(request, invitacion_id):
    invitacion = get_object_or_404(Invitacion, pk=invitacion_id, invitado=request.user, estado='pendiente')
    Suscripcion.objects.create(plan=invitacion.plan, usuario=request.user)
    invitacion.estado = 'aceptada'
    invitacion.save()
    messages.success(request, f'Te has unido al plan {invitacion.plan.nombre}.')
    return redirect('Dashboard')

@login_required
def rechazar_invitacion(request, invitacion_id):
    invitacion = get_object_or_404(Invitacion, pk=invitacion_id, invitado=request.user, estado='pendiente')
    invitacion.estado = 'rechazada'
    invitacion.save()
    messages.info(request, 'Invitación rechazada.')
    return redirect('Dashboard')


@login_required
def edit_profile(request):
    profile_form = ProfileEditForm(instance=request.user)
    password_form = PasswordChangeFormCustom(request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('Dashboard')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeFormCustom(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Contraseña cambiada exitosamente.')
                return redirect('Dashboard')

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'auth/edit_profile.html', context)
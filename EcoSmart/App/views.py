from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

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

            # Send verification email
            subject = 'Bienvenido a EcoSmart - Verifica tu cuenta'
            message = f'Hola {user.first_name},\n\nGracias por registrarte en EcoSmart. Tu cuenta ha sido creada exitosamente.\n\nPara verificar tu email, por favor confirma que este es tu correo electrónico.\n\nSaludos,\nEl equipo de EcoSmart'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, 'Usuario registrado exitosamente. Revisa tu email para verificar tu cuenta.')
            except Exception as e:
                messages.warning(request, 'Usuario registrado, pero hubo un problema enviando el email de verificación.')

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
@login_required
def Inicio(request):
    return render(request, 'menu_principal/index.html')

@login_required
def Mis_Planes(request):
    # Obtener todos los planes del usuario
    suscripciones = request.user.suscripciones.all()
    invitaciones_pendientes = Invitacion.objects.filter(invitado=request.user, estado='pendiente')

    context = {
        'mis_planes': suscripciones,
        'invitaciones_pendientes': invitaciones_pendientes,
    }
    return render(request, 'menu_principal/mis_planes.html', context)

def transacciones(request):
    return render(request, 'menu_principal/transacciones.html')
@login_required
def Estadisticas(request):
    # Obtener todos los planes del usuario
    suscripciones = request.user.suscripciones.all()
    planes_ids = [suscripcion.plan.id for suscripcion in suscripciones]
    
    # Importar modelos necesarios
    from Planes_app.models import Dinero, Ingreso, Gasto, Objetivo
    
    # Calcular estadísticas globales
    total_ingresos = 0
    total_gastos = 0
    total_objetivos = 0
    objetivos_completados = 0
    
    # Obtener todos los dineros de los planes del usuario
    dineros = Dinero.objects.filter(plan_id__in=planes_ids)
    
    for dinero in dineros:
        total_ingresos += dinero.ingreso_total
        total_gastos += dinero.gasto_total
    
    # Calcular objetivos
    objetivos = Objetivo.objects.filter(plan_id__in=planes_ids)
    total_objetivos = objetivos.count()
    objetivos_completados = objetivos.filter(estado='completado').count()
    
    # Balance total
    balance_total = total_ingresos - total_gastos
    
    # Obtener transacciones recientes (últimas 10)
    ingresos_recientes = Ingreso.objects.filter(dinero__plan_id__in=planes_ids).order_by('-fecha_guardado')[:5]
    gastos_recientes = Gasto.objects.filter(dinero__plan_id__in=planes_ids).order_by('-fecha_guardado')[:5]
    
    # Combinar y ordenar transacciones
    transacciones_recientes = []
    for ingreso in ingresos_recientes:
        transacciones_recientes.append({
            'fecha': ingreso.fecha_guardado,
            'descripcion': ingreso.nombre,
            'tipo': 'Ingreso',
            'monto': ingreso.cantidad,
            'plan': ingreso.dinero.plan.nombre
        })
    
    for gasto in gastos_recientes:
        transacciones_recientes.append({
            'fecha': gasto.fecha_guardado,
            'descripcion': gasto.nombre,
            'tipo': 'Gasto',
            'monto': gasto.cantidad,
            'plan': gasto.dinero.plan.nombre
        })
    
    # Ordenar por fecha descendente
    transacciones_recientes.sort(key=lambda x: x['fecha'], reverse=True)
    transacciones_recientes = transacciones_recientes[:10]
    
    # Estadísticas por categoría de gastos
    gastos_por_categoria = {}
    for gasto in Gasto.objects.filter(dinero__plan_id__in=planes_ids):
        categoria = gasto.get_tipo_gasto_display()
        if categoria in gastos_por_categoria:
            gastos_por_categoria[categoria] += gasto.cantidad
        else:
            gastos_por_categoria[categoria] = gasto.cantidad
    
    context = {
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance_total': balance_total,
        'total_objetivos': total_objetivos,
        'objetivos_completados': objetivos_completados,
        'transacciones_recientes': transacciones_recientes,
        'gastos_por_categoria': gastos_por_categoria,
        'planes_count': len(planes_ids),
    }
    
    return render(request, 'menu_principal/Estadisticas.html', context)

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
def invitaciones(request):
    invitaciones_pendientes = Invitacion.objects.filter(invitado=request.user, estado='pendiente').select_related('plan', 'invitador')
    context = {
        'invitaciones_pendientes': invitaciones_pendientes,
    }
    return render(request, 'menu_principal/invitaciones.html', context)


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
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

# --- Importaciones de modelos y formularios ---
# Asegúrate de que estos modelos y formularios estén definidos en sus respectivos archivos.
from .models import Plan, Suscripcion, Dinero, Ingreso, Gasto, Objetivo, Tarea 
from .forms import IngresoForm, GastoForm, ObjetivoForm, TareaForm 

def verificar_membresia(request, plan_id):
    """Función auxiliar para verificar si el usuario pertenece al plan."""
    plan = get_object_or_404(Plan, pk=plan_id)
    es_miembro = Suscripcion.objects.filter(plan=plan, usuario=request.user).exists() or plan.creador == request.user
    return plan, es_miembro

# --- Vistas de la aplicación ---

@login_required
def menu_plan(request, plan_id):
    """Muestra el menú principal del plan y realiza la verificación de membresía."""
    try:
        plan, es_miembro = verificar_membresia(request, plan_id)
    except:
        messages.error(request, 'El plan solicitado no existe.')
        return redirect('dashboard')

    if not es_miembro:
        messages.error(request, 'No tienes acceso a este plan.')
        return redirect('Dashboard') 

    dinero_info, created = Dinero.objects.get_or_create(plan=plan)
    
    context = {
        'plan': plan,
        'dinero_info': dinero_info,
    }
    return render(request, 'menu_plan.html', context)


@login_required
def ingresos(request, plan_id):
    """Gestión y registro de nuevos ingresos."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    dinero_obj = get_object_or_404(Dinero, plan=plan)
    
    if request.method == 'POST':
        form = IngresoForm(request.POST)
        if form.is_valid():
            ingreso = form.save(commit=False)
            ingreso.dinero = dinero_obj
            ingreso.save()
            
            dinero_obj.total_dinero += ingreso.cantidad
            dinero_obj.ingreso_total += ingreso.cantidad
            dinero_obj.save()
            
            messages.success(request, 'Ingreso registrado con éxito.')
            return redirect('ingresos', plan_id=plan.id)
    else:
        form = IngresoForm()

    ingresos_list = Ingreso.objects.filter(dinero=dinero_obj).order_by('-fecha_guardado')

    context = {
        'plan': plan,
        'form': form,
        'ingresos_list': ingresos_list,
        'dinero_info': dinero_obj,
    }
    return render(request, 'ingresos.html', context)


@login_required
def gastos(request, plan_id):
    """Gestión y registro de nuevos gastos."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    dinero_obj = get_object_or_404(Dinero, plan=plan)
    
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.dinero = dinero_obj
            gasto.save()
            
            dinero_obj.total_dinero -= gasto.cantidad
            dinero_obj.gasto_total += gasto.cantidad
            dinero_obj.save()
            
            messages.success(request, 'Gasto registrado con éxito.')
            return redirect('gastos', plan_id=plan.id)
    else:
        form = GastoForm()

    gastos_list = Gasto.objects.filter(dinero=dinero_obj).order_by('-fecha_guardado')

    context = {
        'plan': plan,
        'form': form,
        'gastos_list': gastos_list,
        'dinero_info': dinero_obj,
    }
    return render(request, 'gastos.html', context)


@login_required
def objetivos(request, plan_id):
    """Gestión de Objetivos de Ahorro."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    if request.method == 'POST':
        form = ObjetivoForm(request.POST)
        if form.is_valid():
            objetivo = form.save(commit=False)
            objetivo.plan = plan
            objetivo.save()
            messages.success(request, 'Objetivo creado correctamente.')
            return redirect('Planes_app:objetivos', plan_id=plan.id)
    else:
        form = ObjetivoForm()
    
    objetivos_list = Objetivo.objects.filter(plan=plan).order_by('fecha_guardado')

    context = {
        'plan': plan,
        'objetivos_list': objetivos_list,
        'form': form,
    }
    return render(request, 'objetivos.html', context)


@login_required
def tareas(request, plan_id):
    """Gestión de Tareas y Recordatorios."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    if request.method == 'POST':
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.plan = plan
            tarea.save()
            messages.success(request, 'Tarea agregada correctamente.')
            return redirect('tareas', plan_id=plan.id)
    else:
        form = TareaForm()

    tareas_pendientes = Tarea.objects.filter(plan=plan, estado__in=['pendiente', 'en_proceso']).order_by('fecha_a_completar')
    tareas_completadas = Tarea.objects.filter(plan=plan, estado='completada').order_by('-fecha_guardado')

    context = {
        'plan': plan,
        'form': form,
        'pendientes': tareas_pendientes,
        'completadas': tareas_completadas,
    }
    return render(request, 'tareas.html', context)


@login_required
def estadisticas(request, plan_id):
    """Muestra un resumen de estadísticas financieras."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    dinero_obj = get_object_or_404(Dinero, plan=plan)

    ingresos_por_tipo = Ingreso.objects.filter(dinero=dinero_obj).values('tipo_ingreso').annotate(total=Sum('cantidad'))
    gastos_por_tipo = Gasto.objects.filter(dinero=dinero_obj).values('tipo_gasto').annotate(total=Sum('cantidad'))

    context = {
        'plan': plan,
        'dinero_info': dinero_obj,
        'ingresos_por_tipo': ingresos_por_tipo,
        'gastos_por_tipo': gastos_por_tipo,
    }
    return render(request, 'estadisticas.html', context)
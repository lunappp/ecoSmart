from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction 
from django.utils import timezone
from django.db.models import Sum

# Asumiendo que estas son las importaciones correctas para tus modelos y formularios
from .models import Plan, Suscripcion, Objetivo, Dinero, Gasto, Ingreso, Tarea 
from .forms import ObjetivoForm, AportarObjetivoForm, IngresoForm, GastoForm, TareaForm # Asegúrate que todos estos existen

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


@login_required
def objetivos(request, plan_id):
    """
    Muestra la lista de objetivos del plan y el formulario para agregar uno nuevo.
    """
    plan = get_object_or_404(Plan, pk=plan_id)
    
    # Obtener todos los objetivos asociados a este plan.
    objetivos_del_plan = Objetivo.objects.filter(plan=plan)
    
    # Formulario para agregar un nuevo objetivo
    agregar_form = ObjetivoForm()
    
    # Formulario para aportar dinero a un objetivo
    aportar_form = AportarObjetivoForm()
    
    context = {
        'plan': plan,
        'objetivos_del_plan': objetivos_del_plan,
        'agregar_form': agregar_form,
        'aportar_form': aportar_form,
    }
    return render(request, 'objetivos.html', context)

def aportar_objetivo(request, plan_id, objetivo_id):
    """
    Procesa el aporte de dinero a un Objetivo, registrándolo como Gasto.
    Se usa transaction.atomic() para asegurar la integridad de datos.
    """
    plan = get_object_or_404(Plan, pk=plan_id)
    objetivo = get_object_or_404(Objetivo, pk=objetivo_id)
    
    # Obtener o crear el objeto Dinero
    dinero_plan, created = Dinero.objects.get_or_create(
        plan=plan, 
        # CORRECCIÓN CLAVE: Usar gasto_total e ingreso_total (snake_case)
        defaults={'total_dinero': 0, 'gasto_total': 0, 'ingreso_total': 0}
    )

    if request.method == 'POST':
        form = AportarObjetivoForm(request.POST)
        
        if form.is_valid():
            
            # ATENCIÓN: Se usa 'monto_aportar' basado en el código que enviaste.
            try:
                monto_aporte = form.cleaned_data['monto_aportar']
            except KeyError:
                messages.error(request, "Error interno: El campo 'monto_aportar' no fue encontrado.")
                return redirect('objetivos', plan_id=plan.id)

            
            # --- Ejecutar Transacción Atómica ---
            try:
                with transaction.atomic():
                    
                    if dinero_plan.total_dinero >= monto_aporte:
                        
                        # A. CREAR EL GASTO 
                        Gasto.objects.create(
                            nombre=f"Aporte a Objetivo: {objetivo.nombre}",
                            tipo_gasto='objetivo', 
                            cantidad=monto_aporte,
                            dinero=dinero_plan,
                            # NOTA: Los campos obligatorios ahora son solo los que existen en tu modelo
                        )
                        
                        # B. ACTUALIZAR EL MODELO DINERO
                        dinero_plan.total_dinero -= monto_aporte
                        dinero_plan.gasto_total += monto_aporte # CORRECCIÓN: Usar gasto_total
                        dinero_plan.save()
                        
                        # C. ACTUALIZAR EL OBJETIVO
                        objetivo.monto_actual += monto_aporte
                        objetivo.save()
                        
                        # Mensajes de éxito
                        if objetivo.monto_actual >= objetivo.monto_necesario:
                            messages.success(request, f"¡Objetivo '{objetivo.nombre}' completado! 🎉")
                        else:
                            messages.success(request, f"Se han aportado ${monto_aporte} a tu objetivo y se registró como gasto.")
                    
                    else:
                        messages.error(request, f"Capital insuficiente. Solo tienes ${dinero_plan.total_dinero} disponibles para aportar.")
            
            except Exception as e:
                # Si esto falla de nuevo, el error es otro campo obligatorio en Gasto (ej. fecha, descripcion)
                messages.error(request, f"Ocurrió un error final de la base de datos. Debes revisar los campos obligatorios de Gasto: {e}")
                
        else:
            messages.error(request, 'Error en el formulario. Asegúrate de ingresar una cantidad válida.')

    return redirect('objetivos', plan_id=plan.id)

def agregar_objetivo(request, plan_id):
    """Maneja el formulario POST para agregar un nuevo objetivo."""
    plan = get_object_or_404(Plan, pk=plan_id)
    
    if request.method == 'POST':
        form = ObjetivoForm(request.POST)
        if form.is_valid():
            objetivo = form.save(commit=False)
            objetivo.plan = plan
            # Establecer monto_actual en 0 por defecto al crear
            if objetivo.monto_actual is None:
                objetivo.monto_actual = 0
            objetivo.save()
            messages.success(request, f"Objetivo '{objetivo.nombre}' agregado con éxito.")
        else:
            messages.error(request, 'Error al agregar el objetivo. Verifica los campos.')
    
    return redirect('objetivos', plan_id=plan.id)


# --- VISTAS DE TAREAS (CORREGIDAS) ---

def obtener_estado_tarea(tarea):
    """
    Calcula el estado visual de una tarea.
    - Usa 'estado' para saber si está completada.
    - Usa 'fecha_a_completar' para chequear vencimiento.
    - Usa 'fecha_completado' para chequear si fue A TIEMPO o TARDE.
    """
    hoy_date = timezone.now().date()
    esta_completada = (tarea.estado == 'completada')

    # Si la tarea NO está completada
    if not esta_completada:
        # Tarea VENCIDA: Solo si tiene fecha límite y esta ya pasó
        if tarea.fecha_a_completar and tarea.fecha_a_completar < hoy_date:
            return 'VENCIDA'
        
        # Tarea EN PROCESO (si no está vencida)
        if tarea.estado == 'en_proceso':
            return 'EN_PROCESO'
            
        # Tarea PENDIENTE (el estado por defecto)
        return 'PENDIENTE'

    # Si la tarea SÍ está completada
    else:
        # Si tiene fecha límite, verificamos si fue A TIEMPO o TARDE
        if tarea.fecha_a_completar:
            # CORRECCIÓN DE LÓGICA: Usar la fecha de completado si existe
            fecha_real_completado = tarea.fecha_completado.date() if tarea.fecha_completado else hoy_date
            
            # Comparamos la fecha de completado real contra la fecha límite
            if fecha_real_completado <= tarea.fecha_a_completar:
                return 'COMPLETADA_A_TIEMPO'
            else:
                return 'COMPLETADA_TARDE'
        
        # Si se completó pero no tenía fecha límite
        return 'COMPLETADA_GENERAL'


@login_required
def tareas(request, plan_id):
    # ... (resto de la función 'tareas' es igual)
    plan = get_object_or_404(Plan, pk=plan_id)
    
    # 1. Obtener todas las tareas del plan
    tareas_del_plan = Tarea.objects.filter(plan=plan).order_by('estado', 'fecha_a_completar')
    
    # 2. Adjuntar el estado calculado a cada objeto Tarea
    tareas_con_estado = []
    for tarea in tareas_del_plan:
        tarea.estado_calculado = obtener_estado_tarea(tarea) # Usamos el estado calculado
        tareas_con_estado.append(tarea)
        
    context = {
        'plan': plan,
        'tareas_con_estado': tareas_con_estado,
        'tarea_form': TareaForm(), 
    }
    return render(request, 'tareas.html', context)


@login_required
def agregar_tarea(request, plan_id):
    """Maneja el POST para crear una nueva tarea."""
    plan = get_object_or_404(Plan, pk=plan_id)
    
    if request.method == 'POST':
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.plan = plan
            # El estado ya se establece por defecto a 'pendiente' en el modelo
            tarea.save()
            messages.success(request, f"Tarea '{tarea.nombre}' agregada con éxito.")
        else:
            messages.error(request, 'Error al agregar la tarea. Verifica todos los campos.')
    
    return redirect('tareas', plan_id=plan.id)


@login_required
def cambiar_estado_tarea(request, plan_id, tarea_id):
    """Cambia el estado de una tarea entre 'completada' y 'pendiente', registrando la fecha."""
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    
    if request.method == 'POST':
        
        # Si la tarea NO está completada, la completamos
        if tarea.estado != 'completada':
            tarea.estado = 'completada'
            tarea.fecha_completado = timezone.now() # Registramos la fecha y hora de completado
            tarea.save()
            messages.success(request, f"Tarea '{tarea.nombre}' marcada como completada.")
        else:
            # Si ya está completada, la reabrimos (cambiamos a pendiente)
            tarea.estado = 'pendiente'
            tarea.fecha_completado = None # Eliminamos la fecha de completado
            tarea.save()
            messages.info(request, f"Tarea '{tarea.nombre}' reabierta.")
            
    return redirect('tareas', plan_id=plan_id)
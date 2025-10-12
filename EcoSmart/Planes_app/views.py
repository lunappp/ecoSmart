from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse

# Asumiendo que estas son las importaciones correctas para tus modelos y formularios
from .models import Plan, Suscripcion, Objetivo, Dinero, Gasto, Ingreso, Tarea, Invitacion
from .forms import ObjetivoForm, AportarObjetivoForm, IngresoForm, GastoForm, TareaForm, EditPlanForm # Asegúrate que todos estos existen

User = get_user_model()

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

    # Determinar si el usuario es admin
    es_admin = (plan.creador == request.user or
                Suscripcion.objects.filter(plan=plan, usuario=request.user, rol='admin').exists())

    if request.method == 'POST' and es_admin:
        if 'user_id' in request.POST:
            # Handle invitation
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            if Suscripcion.objects.filter(plan=plan, usuario=user).exists():
                messages.error(request, 'El usuario ya es miembro del plan.')
            else:
                existing = Invitacion.objects.filter(plan=plan, invitado=user).first()
                if existing:
                    if existing.estado == 'pendiente':
                        messages.error(request, 'Ya existe una invitación pendiente para este usuario.')
                    else:
                        existing.estado = 'pendiente'
                        existing.invitador = request.user
                        existing.fecha_invitacion = timezone.now()
                        existing.save()
                        messages.success(request, f'Invitación reenviada a {user.username}.')
                else:
                    Invitacion.objects.create(plan=plan, invitado=user, invitador=request.user)
                    messages.success(request, f'Invitación enviada a {user.username}.')
        elif 'suscripcion_id' in request.POST:
            # Handle member deletion
            suscripcion_id = request.POST.get('suscripcion_id')
            suscripcion = get_object_or_404(Suscripcion, pk=suscripcion_id, plan=plan)
            if suscripcion.usuario != request.user:
                username = suscripcion.usuario.username
                suscripcion.delete()
                messages.success(request, f'Miembro {username} eliminado del plan.')
            else:
                messages.error(request, 'No puedes eliminarte a ti mismo.')

    dinero_info, created = Dinero.objects.get_or_create(plan=plan)

    context = {
        'plan': plan,
        'dinero_info': dinero_info,
        'es_admin': es_admin,
    }
    return render(request, 'menu_plan.html', context)


@login_required
def editar_plan(request, plan_id):
    """Permite editar el nombre, descripción e imagen del plan (solo admin)."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro:
        messages.error(request, 'No tienes acceso a este plan.')
        return redirect('dashboard')

    # Verificar si el usuario es admin o moderador
    es_admin = (plan.creador == request.user or
                Suscripcion.objects.filter(plan=plan, usuario=request.user, rol__in=['admin', 'moderador']).exists())
    if not es_admin:
        messages.error(request, 'Solo los administradores o moderadores pueden editar el plan.')
        return redirect('Menu_plan', plan_id=plan.id)

    if request.method == 'POST':
        if 'delete_plan' in request.POST:
            # Handle plan deletion - only admins can delete
            es_admin_real = (plan.creador == request.user or
                            Suscripcion.objects.filter(plan=plan, usuario=request.user, rol='admin').exists())
            if not es_admin_real:
                messages.error(request, 'Solo los administradores pueden eliminar el plan.')
                return redirect('Menu_plan', plan_id=plan_id)
            try:
                plan_name = plan.nombre
                plan.delete()
                messages.success(request, f'Plan "{plan_name}" eliminado con éxito.')
                return redirect('Dashboard')
            except Exception as e:
                messages.error(request, f'Error al eliminar el plan: {e}')
                return redirect('Menu_plan', plan_id=plan_id)
        else:
            form = EditPlanForm(request.POST, request.FILES, instance=plan)
            if form.is_valid():
                form.save()
                messages.success(request, f'Plan "{plan.nombre}" actualizado con éxito.')
                return redirect('Menu_plan', plan_id=plan.id)
            else:
                messages.error(request, 'Error al editar el plan. Verifica los campos.')
    else:
        form = EditPlanForm(instance=plan)

    context = {
        'plan': plan,
        'form': form,
    }
    return render(request, 'editar_plan.html', context)


@login_required
def ajustes(request, plan_id):
    """Página de ajustes del plan: editar y gestionar miembros."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro:
        messages.error(request, 'No tienes acceso a este plan.')
        return redirect('Dashboard')

    es_admin = (plan.creador == request.user or
                Suscripcion.objects.filter(plan=plan, usuario=request.user, rol__in=['admin', 'moderador']).exists())
    es_admin_real = (plan.creador == request.user or
                     Suscripcion.objects.filter(plan=plan, usuario=request.user, rol='admin').exists())

    if request.method == 'POST':
        if not es_admin:
            messages.error(request, 'Solo los administradores o moderadores pueden realizar cambios en los ajustes.')
            return redirect('ajustes', plan_id=plan.id)
        if 'user_id' in request.POST:
            # Handle invitation
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            if Suscripcion.objects.filter(plan=plan, usuario=user).exists():
                messages.error(request, 'El usuario ya es miembro del plan.')
            else:
                existing = Invitacion.objects.filter(plan=plan, invitado=user).first()
                if existing:
                    if existing.estado == 'pendiente':
                        messages.error(request, 'Ya existe una invitación pendiente para este usuario.')
                    else:
                        existing.estado = 'pendiente'
                        existing.invitador = request.user
                        existing.fecha_invitacion = timezone.now()
                        existing.save()
                        messages.success(request, f'Invitación reenviada a {user.username}.')
                else:
                    Invitacion.objects.create(plan=plan, invitado=user, invitador=request.user)
                    messages.success(request, f'Invitación enviada a {user.username}.')
        elif 'suscripcion_id' in request.POST:
            # Handle member deletion
            suscripcion_id = request.POST.get('suscripcion_id')
            suscripcion = get_object_or_404(Suscripcion, pk=suscripcion_id, plan=plan)
            if suscripcion.usuario != request.user:
                username = suscripcion.usuario.username
                suscripcion.delete()
                messages.success(request, f'Miembro {username} eliminado del plan.')
            else:
                messages.error(request, 'No puedes eliminarte a ti mismo.')
        elif 'promote_suscripcion_id' in request.POST:
            # Handle member promotion
            suscripcion_id = request.POST.get('promote_suscripcion_id')
            suscripcion = get_object_or_404(Suscripcion, pk=suscripcion_id, plan=plan)
            new_rol = request.POST.get('new_rol')
            if suscripcion.usuario == request.user:
                messages.error(request, 'No puedes cambiar tu propio rol.')
            elif new_rol not in ['moderador', 'admin']:
                messages.error(request, 'Rol inválido.')
            else:
                can_promote = False
                user_is_admin = (plan.creador == request.user or
                                 Suscripcion.objects.filter(plan=plan, usuario=request.user, rol='admin').exists())
                user_is_moderator = Suscripcion.objects.filter(plan=plan, usuario=request.user, rol='moderador').exists()
                if user_is_admin:
                    can_promote = True
                elif user_is_moderator and new_rol == 'moderador':
                    can_promote = True
                if can_promote:
                    suscripcion.rol = new_rol
                    suscripcion.save()
                    messages.success(request, f'{suscripcion.usuario.username} ascendido a {suscripcion.get_rol_display()}.')
                else:
                    messages.error(request, 'No tienes permisos para ascender a ese rol.')
        elif 'demote_suscripcion_id' in request.POST:
            # Handle member demotion
            suscripcion_id = request.POST.get('demote_suscripcion_id')
            suscripcion = get_object_or_404(Suscripcion, pk=suscripcion_id, plan=plan)
            if suscripcion.usuario == request.user:
                messages.error(request, 'No puedes cambiar tu propio rol.')
            else:
                user_is_admin = (plan.creador == request.user or
                                 Suscripcion.objects.filter(plan=plan, usuario=request.user, rol='admin').exists())
                if user_is_admin:
                    if suscripcion.rol == 'moderador':
                        suscripcion.rol = 'miembro'
                        suscripcion.save()
                        messages.success(request, f'{suscripcion.usuario.username} degradado a Miembro.')
                    elif suscripcion.rol == 'admin' and plan.creador != suscripcion.usuario:
                        suscripcion.rol = 'moderador'
                        suscripcion.save()
                        messages.success(request, f'{suscripcion.usuario.username} degradado a Moderador.')
                    else:
                        messages.error(request, 'No se puede degradar más.')
                else:
                    messages.error(request, 'Solo administradores pueden degradar miembros.')
        elif 'delete_plan' in request.POST:
            # Handle plan deletion - only admins can delete
            if not es_admin_real:
                messages.error(request, 'Solo los administradores pueden eliminar el plan.')
                return redirect('ajustes', plan_id=plan.id)
            try:
                plan_name = plan.nombre
                plan.delete()
                messages.success(request, f'Plan "{plan_name}" eliminado con éxito.')
                return redirect('Dashboard')
            except Exception as e:
                messages.error(request, f'Error al eliminar el plan: {e}')
        else:
            # Handle plan edit
            form = EditPlanForm(request.POST, request.FILES, instance=plan)
            if form.is_valid():
                form.save()
                messages.success(request, f'Plan "{plan.nombre}" actualizado con éxito.')
            else:
                messages.error(request, 'Error al editar el plan. Verifica los campos.')

    edit_form = EditPlanForm(instance=plan)
    miembros_actuales = None
    invitaciones_enviadas = None
    if plan.tipo_plan == 'grupal':
        miembros_actuales = Suscripcion.objects.filter(plan=plan).select_related('usuario')
        invitaciones_enviadas = Invitacion.objects.filter(plan=plan, invitador=request.user, estado='pendiente')

    context = {
        'plan': plan,
        'edit_form': edit_form,
        'miembros_actuales': miembros_actuales,
        'invitaciones_enviadas': invitaciones_enviadas,
        'es_admin': es_admin,
        'es_admin_real': es_admin_real,
    }
    return render(request, 'ajustes.html', context)


@login_required
def ingresos(request, plan_id):
    """Gestión y registro de nuevos ingresos."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    dinero_obj = get_object_or_404(Dinero, plan=plan)
    
    if request.method == 'POST':
        form = IngresoForm(request.POST, request.FILES)
        if form.is_valid():
            ingreso = form.save(commit=False)
            ingreso.dinero = dinero_obj
            ingreso.user = request.user
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
def editar_ingreso(request, plan_id, ingreso_id):
    """Permite editar un ingreso existente y ajusta los totales de Dinero."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')
    
    ingreso = get_object_or_404(Ingreso, pk=ingreso_id, dinero__plan=plan)
    dinero_obj = ingreso.dinero
    
    if request.method == 'POST':
        form = IngresoForm(request.POST, request.FILES, instance=ingreso)
        if form.is_valid():
            nueva_cantidad = form.cleaned_data['cantidad']
            antigua_cantidad = ingreso.cantidad
            
            # Cálculo de la diferencia
            diferencia = nueva_cantidad - antigua_cantidad

            try:
                with transaction.atomic():
                    # 1. Guardar el ingreso con los nuevos datos
                    form.save() 
                    
                    # 2. Ajustar los totales de Dinero
                    dinero_obj.total_dinero += diferencia
                    dinero_obj.ingreso_total += diferencia
                    dinero_obj.save()
                    
                    messages.success(request, f"Ingreso '{ingreso.nombre}' actualizado con éxito.")
            except Exception as e:
                messages.error(request, f"Error al actualizar el ingreso: {e}")

            return redirect('ingresos', plan_id=plan.id)
    else:
        form = IngresoForm(instance=ingreso)

    context = {
        'plan': plan,
        'form': form,
        'ingreso': ingreso,
    }
    return render(request, 'editar_ingreso.html', context)


@login_required
def eliminar_ingreso(request, plan_id, ingreso_id):
    """Elimina un ingreso existente y ajusta los totales de Dinero."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')
    
    ingreso = get_object_or_404(Ingreso, pk=ingreso_id, dinero__plan=plan)
    dinero_obj = ingreso.dinero
    
    if request.method == 'POST':
        cantidad_a_revertir = ingreso.cantidad

        try:
            with transaction.atomic():
                # 1. Revertir los totales de Dinero
                dinero_obj.total_dinero -= cantidad_a_revertir
                dinero_obj.ingreso_total -= cantidad_a_revertir
                dinero_obj.save()
                
                # 2. Eliminar el ingreso
                ingreso.delete()
                
                messages.success(request, f"Ingreso '{ingreso.nombre}' eliminado con éxito y totales ajustados.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el ingreso: {e}")
            
        return redirect('ingresos', plan_id=plan.id)
    
    context = {'plan': plan, 'ingreso': ingreso}
    return render(request, 'confirmar_eliminar_ingreso.html', context)


@login_required
def gastos(request, plan_id):
    """Gestión y registro de nuevos gastos."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    dinero_obj = get_object_or_404(Dinero, plan=plan)
    
    if request.method == 'POST':
        form = GastoForm(request.POST, request.FILES)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.dinero = dinero_obj
            gasto.user = request.user

            # Validación de fondos antes de guardar el gasto
            if gasto.cantidad > dinero_obj.total_dinero:
                 messages.error(request, 'Capital insuficiente para registrar este gasto.')
                 return redirect('gastos', plan_id=plan.id)

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
def editar_gasto(request, plan_id, gasto_id):
    """Permite editar un gasto existente y ajusta los totales de Dinero."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')
    
    gasto = get_object_or_404(Gasto, pk=gasto_id, dinero__plan=plan)
    dinero_obj = gasto.dinero
    
    if request.method == 'POST':
        form = GastoForm(request.POST, request.FILES, instance=gasto)
        if form.is_valid():
            nueva_cantidad = form.cleaned_data['cantidad']
            antigua_cantidad = gasto.cantidad
            
            # Diferencia (Old - New). Si la diferencia es positiva, se 'añade' dinero, si es negativa, se 'resta'.
            diferencia = antigua_cantidad - nueva_cantidad
            
            # Chequear si la nueva cantidad excede el total disponible (si la diferencia es negativa)
            if dinero_obj.total_dinero + diferencia < 0: # dinero_obj.total_dinero + (antigua - nueva) < 0
                 messages.error(request, 'Capital insuficiente. El nuevo gasto excede el total disponible.')
                 return redirect('editar_gasto', plan_id=plan.id, gasto_id=gasto.id)


            try:
                with transaction.atomic():
                    # 1. Guardar el gasto con los nuevos datos
                    form.save() 
                    
                    # 2. Ajustar los totales de Dinero
                    dinero_obj.total_dinero += diferencia # Si diferencia es positiva (gasto bajó), se suma dinero. Si es negativa (gasto subió), se resta.
                    dinero_obj.gasto_total -= diferencia # Invertido para ajustar el total de gastos
                    dinero_obj.save()
                    
                    messages.success(request, f"Gasto '{gasto.nombre}' actualizado con éxito.")
            except Exception as e:
                messages.error(request, f"Error al actualizar el gasto: {e}")

            return redirect('gastos', plan_id=plan.id)
    else:
        form = GastoForm(instance=gasto)

    context = {
        'plan': plan,
        'form': form,
        'gasto': gasto,
    }
    return render(request, 'editar_gasto.html', context)


@login_required
def eliminar_gasto(request, plan_id, gasto_id):
    """Elimina un gasto existente y ajusta los totales de Dinero, devolviendo el monto."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')
    
    gasto = get_object_or_404(Gasto, pk=gasto_id, dinero__plan=plan)
    dinero_obj = gasto.dinero
    
    if request.method == 'POST':
        cantidad_a_revertir = gasto.cantidad

        try:
            with transaction.atomic():
                # 1. Revertir los totales de Dinero
                dinero_obj.total_dinero += cantidad_a_revertir # Devuelve el dinero al total disponible
                dinero_obj.gasto_total -= cantidad_a_revertir  # Reduce el total de gastos
                dinero_obj.save()
                
                # 2. Eliminar el gasto
                gasto.delete()
                
                messages.success(request, f"Gasto '{gasto.nombre}' eliminado con éxito y monto devuelto al saldo.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el gasto: {e}")
            
        return redirect('gastos', plan_id=plan.id)
    
    context = {'plan': plan, 'gasto': gasto}
    return render(request, 'confirmar_eliminar_gasto.html', context)


@login_required
def estadisticas(request, plan_id):

    """Muestra un resumen de estadísticas financieras."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    dinero_obj = get_object_or_404(Dinero, plan=plan)

    ingresos_por_tipo = Ingreso.objects.filter(dinero=dinero_obj).values('tipo_ingreso').annotate(total=Sum('cantidad'))
    gastos_por_tipo = Gasto.objects.filter(dinero=dinero_obj).values('tipo_gasto').annotate(total=Sum('cantidad'))

    # Estadísticas por usuario
    ingresos_por_usuario = Ingreso.objects.filter(dinero=dinero_obj).values('user__username').annotate(total=Sum('cantidad')).order_by('-total')
    gastos_por_usuario = Gasto.objects.filter(dinero=dinero_obj).values('user__username').annotate(total=Sum('cantidad')).order_by('-total')

    # Listas de ingresos y gastos individuales con usuario
    ingresos_list = Ingreso.objects.filter(dinero=dinero_obj).select_related('user').order_by('-fecha_guardado')
    gastos_list = Gasto.objects.filter(dinero=dinero_obj).select_related('user').order_by('-fecha_guardado')

    context = {
        'plan': plan,
        'dinero_info': dinero_obj,
        'ingresos_por_tipo': ingresos_por_tipo,
        'gastos_por_tipo': gastos_por_tipo,
        'ingresos_por_usuario': ingresos_por_usuario,
        'gastos_por_usuario': gastos_por_usuario,
        'ingresos_list': ingresos_list,
        'gastos_list': gastos_list,
    }
    return render(request, 'estadisticas.html', context)


@login_required
def historiales(request, plan_id):
    """Muestra el historial completo de ingresos y gastos en pestañas."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    dinero_obj = get_object_or_404(Dinero, plan=plan)

    # Listas completas de ingresos y gastos con usuario
    ingresos_list = Ingreso.objects.filter(dinero=dinero_obj).select_related('user').order_by('-fecha_guardado')
    gastos_list = Gasto.objects.filter(dinero=dinero_obj).select_related('user').order_by('-fecha_guardado')

    # Preparar datos para los gráficos de balance diario (último mes), mensual y anual
    from collections import defaultdict
    from datetime import datetime, date
    from django.utils import timezone
    from calendar import monthrange

    hoy = timezone.now().date()
    anio_actual = hoy.year

    # Obtener todas las transacciones ordenadas por fecha
    ingresos = Ingreso.objects.filter(dinero=dinero_obj).order_by('fecha_guardado')
    gastos = Gasto.objects.filter(dinero=dinero_obj).order_by('fecha_guardado')

    # Combinar en una lista de tuplas (fecha, cantidad) donde cantidad es positiva para ingresos, negativa para gastos
    transacciones = []
    for ingreso in ingresos:
        transacciones.append((ingreso.fecha_guardado, float(ingreso.cantidad)))
    for gasto in gastos:
        transacciones.append((gasto.fecha_guardado, -float(gasto.cantidad)))

    # Ordenar por fecha
    transacciones.sort(key=lambda x: x[0])

    # Calcular balance acumulado por mes y año
    balance_por_mes = defaultdict(float)
    balance_por_anio = defaultdict(float)
    balance_acumulado = 0

    for fecha, cantidad in transacciones:
        balance_acumulado += cantidad
        mes = fecha.strftime('%Y-%m')
        anio = fecha.strftime('%Y')
        balance_por_mes[mes] = balance_acumulado
        balance_por_anio[anio] = balance_acumulado

    # Preparar datos para el gráfico mensual (balance al final de cada mes del año actual)
    monthly_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    monthly_data = []

    # Calcular balance acumulado al final de cada mes
    balance_por_mes = {}
    balance_acumulado = 0

    # Para meses pasados, calcular basado en transacciones
    for fecha, cantidad in transacciones:
        if fecha.year == anio_actual:
            balance_acumulado += cantidad
            mes_num = fecha.month
            balance_por_mes[mes_num] = balance_acumulado

    # Para el mes actual, usar el total_dinero actual
    mes_actual_num = hoy.month
    balance_por_mes[mes_actual_num] = float(dinero_obj.total_dinero)

    # Para cada mes, usar el balance si existe, sino 0
    for m in range(1, 13):
        if m in balance_por_mes:
            monthly_data.append(round(balance_por_mes[m], 2))
        else:
            monthly_data.append(0)

    # Preparar datos para el gráfico anual
    yearly_labels = []
    yearly_data = []
    for anio in sorted(balance_por_anio.keys()):
        yearly_labels.append(anio)
        yearly_data.append(round(balance_por_anio[anio], 2))

    # Preparar datos para el gráfico diario del mes actual (balance al final de cada día)
    mes_actual = hoy.strftime('%Y-%m')
    _, dias_en_mes = monthrange(hoy.year, hoy.month)

    daily_labels = []
    daily_data = []

    # Filtrar transacciones del mes actual
    transacciones_mes = [t for t in transacciones if t[0].strftime('%Y-%m') == mes_actual]

    # Calcular el balance al inicio del mes
    balance_inicio_mes = float(dinero_obj.total_dinero)
    for _, cantidad in transacciones_mes:
        balance_inicio_mes -= cantidad

    # Calcular balance acumulado al final de cada día que ha ocurrido
    balance_por_dia = {}
    balance_acumulado = balance_inicio_mes

    dia_actual = hoy.day
    for dia in range(1, dia_actual + 1):
        # Sumar transacciones de este día
        transacciones_dia = [t for t in transacciones_mes if t[0].day == dia]
        for _, cantidad in transacciones_dia:
            balance_acumulado += cantidad
        balance_por_dia[dia] = balance_acumulado

    # Solo incluir días que han ocurrido
    for dia in range(1, dia_actual + 1):
        daily_labels.append(str(dia))
        daily_data.append(round(balance_por_dia.get(dia, balance_inicio_mes), 2))

    import json
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    context = {
        'plan': plan,
        'ingresos_list': ingresos_list,
        'gastos_list': gastos_list,
        'current_year': anio_actual,
        'current_month': meses[hoy.month - 1],
        'daily_labels_json': json.dumps(daily_labels),
        'daily_data_json': json.dumps(daily_data),
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_data_json': json.dumps(monthly_data),
        'yearly_labels_json': json.dumps(yearly_labels),
        'yearly_data_json': json.dumps(yearly_data),
    }
    return render(request, 'historiales.html', context)


@login_required
def objetivos(request, plan_id):
    """
    Muestra la lista de objetivos del plan y el formulario para agregar uno nuevo (solo para admins).
    """
    plan = get_object_or_404(Plan, pk=plan_id)

    # Verificar si mostrar objetivos completados
    show_completed = request.GET.get('show_completed', 'no') == 'yes'

    # Obtener objetivos asociados a este plan, filtrando completados si no se muestran
    if show_completed:
        objetivos_del_plan = Objetivo.objects.filter(plan=plan)
    else:
        objetivos_del_plan = Objetivo.objects.filter(plan=plan).exclude(estado='completado')

    # Verificar si el usuario es admin o moderador
    es_admin = (plan.creador == request.user or
                Suscripcion.objects.filter(plan=plan, usuario=request.user, rol__in=['admin', 'moderador']).exists())
    es_admin_real = (plan.creador == request.user or
                     Suscripcion.objects.filter(plan=plan, usuario=request.user, rol='admin').exists())

    # Formulario para agregar un nuevo objetivo (solo si es admin)
    agregar_form = ObjetivoForm() if es_admin else None

    # Formulario para aportar dinero a un objetivo
    aportar_form = AportarObjetivoForm()

    # Calcular estadísticas de contribución para cada objetivo
    objetivos_con_estadisticas = []
    for objetivo in objetivos_del_plan:
        # Obtener gastos relacionados con este objetivo
        gastos_objetivo = Gasto.objects.filter(
            dinero__plan=plan,
            tipo_gasto='objetivo',
            nombre__icontains=f"Aporte a Objetivo: {objetivo.nombre}"
        ).select_related('user')

        # Agrupar por usuario y sumar contribuciones
        contribuciones_por_usuario = {}
        for gasto in gastos_objetivo:
            user_id = gasto.user.id
            username = gasto.user.username
            if user_id not in contribuciones_por_usuario:
                contribuciones_por_usuario[user_id] = {
                    'username': username,
                    'total': 0
                }
            contribuciones_por_usuario[user_id]['total'] += gasto.cantidad

        # Encontrar máximo y mínimo contribuyente
        if contribuciones_por_usuario:
            max_contribuyente = max(contribuciones_por_usuario.values(), key=lambda x: x['total'])
            min_contribuyente = min(contribuciones_por_usuario.values(), key=lambda x: x['total'])

            # Mostrar estadísticas si hay al menos un contribuyente
            objetivo.contribuciones_stats = {
                'max': max_contribuyente,
                'min': min_contribuyente,
                'total_contribuyentes': len(contribuciones_por_usuario),
                'total_aportado': sum(c['total'] for c in contribuciones_por_usuario.values())
            }
        else:
            objetivo.contribuciones_stats = None

        objetivos_con_estadisticas.append(objetivo)

    context = {
        'plan': plan,
        'objetivos_del_plan': objetivos_con_estadisticas,
        'agregar_form': agregar_form,
        'aportar_form': aportar_form,
        'show_completed': show_completed,
        'es_admin': es_admin,
    }
    return render(request, 'objetivos.html', context)

@login_required
def agregar_objetivo(request, plan_id):
    """Maneja el formulario POST para agregar un nuevo objetivo."""
    plan = get_object_or_404(Plan, pk=plan_id)

    # Verificar si el usuario es admin o moderador del plan
    es_admin = (plan.creador == request.user or
                Suscripcion.objects.filter(plan=plan, usuario=request.user, rol__in=['admin', 'moderador']).exists())
    if not es_admin:
        messages.error(request, 'Solo los administradores o moderadores pueden crear objetivos.')
        return redirect('objetivos', plan_id=plan.id)

    if request.method == 'POST':
        form = ObjetivoForm(request.POST, request.FILES)
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

    # Preservar el parámetro show_completed
    from django.urls import reverse
    show_param = '?show_completed=yes' if request.GET.get('show_completed') == 'yes' else ''
    return redirect(reverse('objetivos', kwargs={'plan_id': plan.id}) + show_param)


@login_required
def editar_objetivo(request, plan_id, objetivo_id):
    """Permite editar un objetivo existente."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    objetivo = get_object_or_404(Objetivo, pk=objetivo_id, plan=plan)

    if request.method == 'POST':
        form = ObjetivoForm(request.POST, request.FILES, instance=objetivo)
        if form.is_valid():
            form.save()
            messages.success(request, f"Objetivo '{objetivo.nombre}' actualizado con éxito.")
            return redirect('objetivos', plan_id=plan.id)
        else:
            messages.error(request, 'Error al editar el objetivo. Verifica los campos.')
    else:
        form = ObjetivoForm(instance=objetivo)

    context = {
        'plan': plan,
        'form': form,
        'objetivo': objetivo,
    }
    return render(request, 'editar_objetivo.html', context)


@login_required
def eliminar_objetivo(request, plan_id, objetivo_id):
    """Elimina un objetivo y devuelve su monto_actual al total de dinero del plan."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    objetivo = get_object_or_404(Objetivo, pk=objetivo_id, plan=plan)
    dinero_obj = get_object_or_404(Dinero, plan=plan)

    if request.method == 'POST':
        completar = request.POST.get('completar') == 'yes'
        monto_a_devolver = objetivo.monto_actual if not completar else 0

        try:
            with transaction.atomic():
                if completar:
                    # Marcar como completado antes de eliminar
                    objetivo.estado = 'completado'
                    objetivo.save()

                # 1. Devolver el monto acumulado al total disponible del plan (solo si no es completado)
                if monto_a_devolver > 0:
                    dinero_obj.total_dinero += monto_a_devolver
                    # Revertir el gasto_total (ya que la aportación se registró como gasto)
                    dinero_obj.gasto_total -= monto_a_devolver
                    dinero_obj.save()
                    messages.info(request, f"${monto_a_devolver} devueltos al saldo disponible.")

                # 2. Eliminar el objetivo
                objetivo.delete()

                if completar:
                    messages.success(request, f"¡Objetivo '{objetivo.nombre}' completado y eliminado! 🎉")
                else:
                    messages.success(request, f"Objetivo '{objetivo.nombre}' eliminado correctamente.")

        except Exception as e:
            messages.error(request, f"Error al eliminar el objetivo: {e}")

        # Preservar el parámetro show_completed
        from django.urls import reverse
        show_param = '?show_completed=yes' if request.GET.get('show_completed') == 'yes' else ''
        return redirect(reverse('objetivos', kwargs={'plan_id': plan.id}) + show_param)

    context = {'plan': plan, 'objetivo': objetivo}
    return render(request, 'confirmar_eliminar_objetivo.html', context)


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
                            user=request.user,
                            imagen=objetivo.imagen,  # Usar la imagen del objetivo
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
                        messages.success(request, f"Se han aportado ${monto_aporte} a tu objetivo y se registró como gasto.")
                        
                    else:
                        messages.error(request, f"Capital insuficiente. Solo tienes ${dinero_plan.total_dinero} disponibles para aportar.")
            
            except Exception as e:
                # Si esto falla de nuevo, el error es otro campo obligatorio en Gasto (ej. fecha, descripcion)
                messages.error(request, f"Ocurrió un error final de la base de datos. Debes revisar los campos obligatorios de Gasto: {e}")
                
        else:
            messages.error(request, 'Error en el formulario. Asegúrate de ingresar una cantidad válida.')

    # Preservar el parámetro show_completed
    from django.urls import reverse
    show_param = '?show_completed=yes' if request.GET.get('show_completed') == 'yes' else ''
    return redirect(reverse('objetivos', kwargs={'plan_id': plan.id}) + show_param)


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
            # Tomamos solo la parte de la fecha si existe fecha_completado, si no, usamos hoy
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
    """Muestra la lista de tareas del plan y el formulario para agregar una nueva."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro:
        messages.error(request, 'No tienes acceso a este plan.')
        return redirect('dashboard')

    # Determinar si el usuario es admin o moderador
    es_admin = (plan.creador == request.user or
                Suscripcion.objects.filter(plan=plan, usuario=request.user, rol__in=['admin', 'moderador']).exists())

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
        'tarea_form': TareaForm(plan=plan),
        'es_admin': es_admin,
    }
    return render(request, 'tareas.html', context)


@login_required
def agregar_tarea(request, plan_id):
    """Maneja el POST para crear una nueva tarea."""
    plan = get_object_or_404(Plan, pk=plan_id)

    if request.method == 'POST':
        form = TareaForm(request.POST, request.FILES, plan=plan)
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
def editar_tarea(request, plan_id, tarea_id):
    """Permite editar una tarea existente, gestionando la fecha de completado si el estado cambia."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    tarea = get_object_or_404(Tarea, pk=tarea_id, plan=plan)

    if request.method == 'POST':
        form = TareaForm(request.POST, request.FILES, instance=tarea, plan=plan)
        if form.is_valid():
            nueva_tarea = form.save(commit=False)
            nuevo_estado = nueva_tarea.estado

            # Lógica para gestionar la fecha_completado
            if nuevo_estado == 'completada' and tarea.estado != 'completada':
                nueva_tarea.fecha_completado = timezone.now()
            elif nuevo_estado != 'completada' and tarea.estado == 'completada':
                nueva_tarea.fecha_completado = None

            nueva_tarea.save()
            messages.success(request, f"Tarea '{nueva_tarea.nombre}' actualizada con éxito.")
            return redirect('tareas', plan_id=plan.id)
        else:
            messages.error(request, 'Error al editar la tarea. Verifica los campos.')
    else:
        form = TareaForm(instance=tarea, plan=plan)

    context = {
        'plan': plan,
        'form': form,
        'tarea': tarea,
    }
    return render(request, 'editar_tarea.html', context)


@login_required
def eliminar_tarea(request, plan_id, tarea_id):
    """Elimina una tarea existente."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    tarea = get_object_or_404(Tarea, pk=tarea_id, plan=plan)

    if request.method == 'POST':
        try:
            tarea.delete()
            messages.success(request, f"Tarea '{tarea.nombre}' eliminada correctamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar la tarea: {e}")
        
        return redirect('tareas', plan_id=plan.id)

    context = {'plan': plan, 'tarea': tarea}
    return render(request, 'confirmar_eliminar_tarea.html', context)


@login_required
def cambiar_estado_tarea(request, plan_id, tarea_id):
    """Cambia el estado de una tarea entre 'completada' y 'pendiente', registrando la fecha."""
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    plan = tarea.plan

    # Verificar membresía al plan
    es_miembro = Suscripcion.objects.filter(plan=plan, usuario=request.user).exists() or plan.creador == request.user
    if not es_miembro:
        messages.error(request, 'No tienes acceso a este plan.')
        return redirect('dashboard')

    # Determinar si el usuario es admin o moderador
    es_admin = (plan.creador == request.user or
                Suscripcion.objects.filter(plan=plan, usuario=request.user, rol__in=['admin', 'moderador']).exists())

    if request.method == 'POST':

        # Verificar si el usuario puede completar esta tarea (admin puede completar cualquier tarea)
        if tarea.usuario_asignado and tarea.usuario_asignado != request.user and not es_admin:
            messages.error(request, f"No puedes completar esta tarea. Solo {tarea.usuario_asignado.username} puede completarla.")
            return redirect('tareas', plan_id=plan_id)

        # Si la tarea NO está completada, la completamos
        if tarea.estado != 'completada':
            tarea.estado = 'completada'
            tarea.fecha_completado = timezone.now() # Registramos la fecha y hora de completado
            tarea.save()
            messages.success(request, f"Tarea '{tarea.nombre}' marcada como completada.")
        else:
            # Si ya está completada, verificar si es admin para reabrir
            if not es_admin:
                messages.error(request, 'Solo los administradores pueden reabrir tareas.')
                return redirect('tareas', plan_id=plan_id)
            # Reabrir la tarea
            tarea.estado = 'pendiente'
            tarea.fecha_completado = None # Eliminamos la fecha de completado
            tarea.save()
            messages.info(request, f"Tarea '{tarea.nombre}' reabierta.")

    return redirect('tareas', plan_id=plan_id)




@login_required
def buscar_usuarios(request, plan_id):
    """Busca usuarios para invitar (solo admin)."""
    try:
        plan, es_miembro = verificar_membresia(request, plan_id)
        if not es_miembro:
            return JsonResponse({'error': 'No autorizado'}, status=403)

        es_admin = (plan.creador == request.user or
                    Suscripcion.objects.filter(plan=plan, usuario=request.user, rol__in=['admin', 'moderador']).exists())

        if not es_admin:
            return JsonResponse({'error': 'No autorizado'}, status=403)

        query = request.GET.get('q', '')
        if len(query) < 1:  # Cambiar a 1 para permitir búsqueda por ID de un dígito
            return JsonResponse([], safe=False)

        usuarios_miembros = Suscripcion.objects.filter(plan=plan).values_list('usuario', flat=True)
        # Buscar por username o por ID si query es numérico
        filter_q = Q(username__icontains=query)
        if query.isdigit():
            filter_q |= Q(id=query)
        usuarios = User.objects.filter(filter_q).exclude(id__in=usuarios_miembros).exclude(id=request.user.id)[:10]

        data = [{'id': u.id, 'username': u.username, 'email': u.email} for u in usuarios]
        return JsonResponse(data, safe=False)
    except Exception as e:

        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@login_required
def cancelar_invitacion(request, plan_id, invitacion_id):
    """Cancela una invitación pendiente."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro:
        messages.error(request, 'No tienes acceso a este plan.')
        return redirect('Dashboard')

    invitacion = get_object_or_404(Invitacion, pk=invitacion_id, plan=plan, invitador=request.user)
    invitacion.delete()
    messages.success(request, f'Invitación a {invitacion.invitado.username} cancelada.')
    return redirect('Menu_plan', plan_id=plan.id)

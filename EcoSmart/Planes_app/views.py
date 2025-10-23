from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponse

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
    """Redirige directamente a las estadísticas del plan."""
    try:
        plan, es_miembro = verificar_membresia(request, plan_id)
    except:
        messages.error(request, 'El plan solicitado no existe.')
        return redirect('dashboard')

    if not es_miembro:
        messages.error(request, 'No tienes acceso a este plan.')
        return redirect('Dashboard')

    # Redirigir directamente a estadísticas
    return redirect('estadisticas', plan_id=plan.id)


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

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'ajustes_partial.html', context)

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

    # Calcular estadísticas adicionales
    ingresos_por_tipo = Ingreso.objects.filter(dinero=dinero_obj).values('tipo_ingreso').annotate(total=Sum('cantidad')).order_by('-total')

    context = {
        'plan': plan,
        'form': form,
        'ingresos_list': ingresos_list,
        'dinero_info': dinero_obj,
        'ingresos_por_tipo': ingresos_por_tipo,
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'ingresos_partial.html', context)
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

    # Calcular estadísticas adicionales
    gastos_por_tipo = Gasto.objects.filter(dinero=dinero_obj).values('tipo_gasto').annotate(total=Sum('cantidad')).order_by('-total')

    context = {
        'plan': plan,
        'form': form,
        'gastos_list': gastos_list,
        'dinero_info': dinero_obj,
        'gastos_por_tipo': gastos_por_tipo,
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'gastos_partial.html', context)
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

    dinero_obj, created = Dinero.objects.get_or_create(plan=plan, defaults={'total_dinero': 0, 'gasto_total': 0, 'ingreso_total': 0})

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
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'estadisticas_partial.html', context)
    return render(request, 'estadisticas.html', context)


@login_required
def historiales(request, plan_id):
    """Muestra el historial completo de ingresos y gastos en pestañas."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro: return redirect('dashboard')

    # Preparar datos para los gráficos de balance diario (último mes), mensual y anual
    from collections import defaultdict
    from datetime import datetime, date
    from django.utils import timezone
    from calendar import monthrange

    hoy = timezone.now().date()
    anio_actual = hoy.year

    # Obtener parámetros de mes y año seleccionados
    selected_month = request.GET.get('month')
    selected_year_param = request.GET.get('year')

    if selected_month:
        try:
            selected_date = datetime.strptime(selected_month, '%Y-%m')
            selected_year = selected_date.year
            selected_month_num = selected_date.month
        except ValueError:
            selected_month = None
            selected_year = int(selected_year_param) if selected_year_param else hoy.year
            selected_month_num = None
    else:
        selected_year = int(selected_year_param) if selected_year_param else hoy.year
        selected_month_num = None

    dinero_obj = get_object_or_404(Dinero, plan=plan)

    # Estadísticas por tipo
    ingresos_por_tipo = Ingreso.objects.filter(dinero=dinero_obj).values('tipo_ingreso').annotate(total=Sum('cantidad'))
    gastos_por_tipo = Gasto.objects.filter(dinero=dinero_obj).values('tipo_gasto').annotate(total=Sum('cantidad'))

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

    # Preparar datos para el gráfico mensual (balance al final de cada mes del año seleccionado)
    monthly_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    monthly_data = []

    # Calcular balance acumulado al final de cada mes
    balance_por_mes = {}
    balance_acumulado = 0

    # Para meses pasados, calcular basado en transacciones
    for fecha, cantidad in transacciones:
        if fecha.year == selected_year:
            balance_acumulado += cantidad
            mes_num = fecha.month
            balance_por_mes[mes_num] = balance_acumulado

    # Para el mes actual si es el año actual, usar el total_dinero actual
    if selected_year == hoy.year:
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

    # Preparar datos para el gráfico diario del mes seleccionado o actual
    if selected_month:
        mes_seleccionado = selected_month
        anio_seleccionado = selected_year
        mes_num_seleccionado = selected_month_num
        # Para el mes actual, mostrar días hasta hoy; para meses pasados, mostrar todos los días
        if selected_month == hoy.strftime('%Y-%m'):
            dia_actual = hoy.day
        else:
            dia_actual = None
    else:
        mes_seleccionado = hoy.strftime('%Y-%m')
        anio_seleccionado = hoy.year
        mes_num_seleccionado = hoy.month
        dia_actual = hoy.day

    _, dias_en_mes = monthrange(anio_seleccionado, mes_num_seleccionado)

    daily_labels = []
    daily_data = []

    # Filtrar transacciones del mes seleccionado
    transacciones_mes = [t for t in transacciones if t[0].strftime('%Y-%m') == mes_seleccionado]

    if transacciones_mes:
        # Calcular el balance al inicio del mes seleccionado
        # Para meses pasados, necesitamos calcular el balance histórico
        if selected_month and selected_month != hoy.strftime('%Y-%m'):
            # Calcular balance histórico al inicio del mes seleccionado
            transacciones_anteriores = [t for t in transacciones if t[0] < transacciones_mes[0][0]]
            balance_inicio_mes = 0
            for _, cantidad in transacciones_anteriores:
                balance_inicio_mes += cantidad
        else:
            # Mes actual: usar total_dinero actual
            balance_inicio_mes = float(dinero_obj.total_dinero)
            for _, cantidad in transacciones_mes:
                balance_inicio_mes -= cantidad

        # Calcular balance acumulado al final de cada día
        balance_por_dia = {}
        balance_acumulado = balance_inicio_mes

        if selected_month and selected_month != hoy.strftime('%Y-%m'):
            # Para meses pasados, mostrar todos los días del mes con datos
            for dia in range(1, dias_en_mes + 1):
                transacciones_dia = [t for t in transacciones_mes if t[0].day == dia]
                for _, cantidad in transacciones_dia:
                    balance_acumulado += cantidad
                if transacciones_dia:  # Solo incluir días que tuvieron transacciones
                    balance_por_dia[dia] = balance_acumulado

            for dia in sorted(balance_por_dia.keys()):
                daily_labels.append(str(dia))
                daily_data.append(round(balance_por_dia[dia], 2))
        else:
            # Mes actual: mostrar días hasta hoy
            if dia_actual:
                for dia in range(1, dia_actual + 1):
                    transacciones_dia = [t for t in transacciones_mes if t[0].day == dia]
                    for _, cantidad in transacciones_dia:
                        balance_acumulado += cantidad
                    balance_por_dia[dia] = balance_acumulado

                for dia in range(1, dia_actual + 1):
                    daily_labels.append(str(dia))
                    daily_data.append(round(balance_por_dia.get(dia, balance_inicio_mes), 2))
    else:
        # No hay transacciones para este mes
        daily_labels = []
        daily_data = []

    # Generar lista de años disponibles (años que tienen transacciones)
    anios_disponibles = set()
    for fecha, _ in transacciones:
        anios_disponibles.add(fecha.year)

    # Agregar año actual si no tiene transacciones pero queremos mostrarlo
    if hoy.year not in anios_disponibles:
        anios_disponibles.add(hoy.year)

    anios_disponibles = sorted(list(anios_disponibles), reverse=True)  # Más recientes primero

    # Generar lista de meses disponibles (meses que tienen transacciones)
    meses_disponibles = set()
    for fecha, _ in transacciones:
        meses_disponibles.add(fecha.strftime('%Y-%m'))

    # Agregar mes actual si no tiene transacciones pero queremos mostrarlo
    mes_actual_str = hoy.strftime('%Y-%m')
    if mes_actual_str not in meses_disponibles:
        meses_disponibles.add(mes_actual_str)

    meses_disponibles = sorted(list(meses_disponibles), reverse=True)  # Más recientes primero

    # Generar lista de meses disponibles hasta el mes actual
    from datetime import datetime
    hoy = timezone.now().date()
    current_year = hoy.year
    current_month = hoy.month

    all_months_for_year = []
    if selected_year < current_year:
        # Si el año seleccionado es anterior, mostrar todos los meses
        for m in range(1, 13):
            month_str = f"{selected_year}-{m:02d}"
            all_months_for_year.append(month_str)
    elif selected_year == current_year:
        # Si es el año actual, mostrar solo hasta el mes actual
        for m in range(1, current_month + 1):
            month_str = f"{selected_year}-{m:02d}"
            all_months_for_year.append(month_str)
    else:
        # Si es un año futuro, mostrar meses desde agosto del año actual en adelante
        if selected_year == current_year:
            # Para el año actual, mostrar desde agosto hasta el mes actual
            for m in range(8, current_month + 1):
                month_str = f"{selected_year}-{m:02d}"
                all_months_for_year.append(month_str)
        else:
            # Para años futuros, mostrar todos los meses desde enero
            for m in range(1, 13):
                month_str = f"{selected_year}-{m:02d}"
                all_months_for_year.append(month_str)

    import json
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    context = {
        'plan': plan,
        'ingresos_por_tipo': ingresos_por_tipo,
        'gastos_por_tipo': gastos_por_tipo,
        'ingresos_list': ingresos_list,
        'gastos_list': gastos_list,
        'current_year': anio_actual,
        'current_month': meses[hoy.month - 1],
        'selected_month': selected_month,
        'selected_year': selected_year,
        'meses_disponibles': meses_disponibles,
        'all_months_for_year': all_months_for_year,
        'anios_disponibles': anios_disponibles,
        'hoy_str': hoy.strftime('%Y-%m'),
        'daily_labels_json': json.dumps(daily_labels),
        'daily_data_json': json.dumps(daily_data),
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_data_json': json.dumps(monthly_data),
        'yearly_labels_json': json.dumps(yearly_labels),
        'yearly_data_json': json.dumps(yearly_data),
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'historiales_partial.html', context)
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
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'objetivos_partial.html', context)
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

    # 3. Obtener miembros del plan para el filtro (todos los usuarios que son miembros)
    plan_members = []
    # Agregar el creador siempre
    plan_members.append({
        'usuario': plan.creador,
        'rol': 'admin'
    })
    # Agregar otros miembros de las suscripciones
    subscriptions = Suscripcion.objects.filter(plan=plan).select_related('usuario')
    for sub in subscriptions:
        if sub.usuario != plan.creador:  # Evitar duplicados
            plan_members.append({
                'usuario': sub.usuario,
                'rol': sub.rol
            })
    # Ordenar por username
    plan_members = sorted(plan_members, key=lambda x: x['usuario'].username)

    # 4. Obtener tareas del usuario actual para "Mis tareas"
    user_tasks = [tarea for tarea in tareas_con_estado if tarea.usuario_asignado == request.user]

    context = {
        'plan': plan,
        'tareas_con_estado': tareas_con_estado,
        'tarea_form': TareaForm(plan=plan),
        'es_admin': es_admin,
        'plan_members': plan_members,
        'user_tasks': user_tasks,
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'tareas_partial.html', context)
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
            tarea.fecha_completado = timezone.now()  # Registramos la fecha y hora de completado
            tarea.save()
            messages.success(request, f"Tarea '{tarea.nombre}' marcada como completada.")
        else:
            # Si ya está completada, verificar si es admin para reabrir
            if not es_admin:
                messages.error(request, 'Solo los administradores pueden reabrir tareas.')
                return redirect('tareas', plan_id=plan_id)
            # Reabrir la tarea
            tarea.estado = 'pendiente'
            tarea.fecha_completado = None  # Eliminamos la fecha de completado
            tarea.save()
            messages.info(request, f"Tarea '{tarea.nombre}' reabierta.")

    return redirect('tareas', plan_id=plan_id)


@login_required
def descargar_pdf_graficos(request, plan_id):
            """Genera y descarga un PDF con los gráficos actuales."""
            plan, es_miembro = verificar_membresia(request, plan_id)
            if not es_miembro:
                return HttpResponse('No autorizado', status=403)

            import matplotlib
            matplotlib.use('Agg')  # Set non-GUI backend
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
            from reportlab.lib.units import inch
            import matplotlib.pyplot as plt
            import io
            import base64
        
            # Obtener parámetros actuales
            selected_month = request.GET.get('month')
            selected_year_param = request.GET.get('year')
        
            # Preparar datos (reutilizar lógica de historiales)
            from collections import defaultdict
            from datetime import datetime, date
            from django.utils import timezone
            from calendar import monthrange
        
            hoy = timezone.now().date()
            anio_actual = hoy.year
        
            if selected_month:
                try:
                    selected_date = datetime.strptime(selected_month, '%Y-%m')
                    selected_year = selected_date.year
                    selected_month_num = selected_date.month
                except ValueError:
                    selected_month = None
                    selected_year = int(selected_year_param) if selected_year_param else hoy.year
                    selected_month_num = None
            else:
                selected_year = int(selected_year_param) if selected_year_param else hoy.year
                selected_month_num = None
        
            dinero_obj = get_object_or_404(Dinero, plan=plan)
        
            # Obtener transacciones
            ingresos = Ingreso.objects.filter(dinero=dinero_obj).order_by('fecha_guardado')
            gastos = Gasto.objects.filter(dinero=dinero_obj).order_by('fecha_guardado')
        
            transacciones = []
            for ingreso in ingresos:
                transacciones.append((ingreso.fecha_guardado, float(ingreso.cantidad)))
            for gasto in gastos:
                transacciones.append((gasto.fecha_guardado, -float(gasto.cantidad)))
        
            transacciones.sort(key=lambda x: x[0])
        
            # Preparar datos para gráficos
            balance_por_mes = {}
            balance_acumulado = 0
        
            for fecha, cantidad in transacciones:
                if fecha.year == selected_year:
                    balance_acumulado += cantidad
                    mes_num = fecha.month
                    balance_por_mes[mes_num] = balance_acumulado
        
            if selected_year == hoy.year:
                mes_actual_num = hoy.month
                balance_por_mes[mes_actual_num] = float(dinero_obj.total_dinero)
        
            monthly_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            monthly_data = []
            for m in range(1, 13):
                if m in balance_por_mes:
                    monthly_data.append(round(balance_por_mes[m], 2))
                else:
                    monthly_data.append(0)
        
            # Preparar datos diarios
            if selected_month:
                mes_seleccionado = selected_month
                anio_seleccionado = selected_year
                mes_num_seleccionado = selected_month_num
                dia_actual = None
            else:
                mes_seleccionado = hoy.strftime('%Y-%m')
                anio_seleccionado = hoy.year
                mes_num_seleccionado = hoy.month
                dia_actual = hoy.day
        
            _, dias_en_mes = monthrange(anio_seleccionado, mes_num_seleccionado)
        
            daily_labels = []
            daily_data = []
        
            transacciones_mes = [t for t in transacciones if t[0].strftime('%Y-%m') == mes_seleccionado]
        
            if transacciones_mes:
                if selected_month and selected_month != hoy.strftime('%Y-%m'):
                    transacciones_anteriores = [t for t in transacciones if t[0] < transacciones_mes[0][0]]
                    balance_inicio_mes = 0
                    for _, cantidad in transacciones_anteriores:
                        balance_inicio_mes += cantidad
                else:
                    balance_inicio_mes = float(dinero_obj.total_dinero)
                    for _, cantidad in transacciones_mes:
                        balance_inicio_mes -= cantidad
        
                balance_por_dia = {}
                balance_acumulado = balance_inicio_mes
        
                if selected_month and selected_month != hoy.strftime('%Y-%m'):
                    for dia in range(1, dias_en_mes + 1):
                        transacciones_dia = [t for t in transacciones_mes if t[0].day == dia]
                        for _, cantidad in transacciones_dia:
                            balance_acumulado += cantidad
                        if transacciones_dia:
                            balance_por_dia[dia] = balance_acumulado
        
                    for dia in sorted(balance_por_dia.keys()):
                        daily_labels.append(str(dia))
                        daily_data.append(round(balance_por_dia[dia], 2))
                else:
                    if dia_actual:
                        for dia in range(1, dia_actual + 1):
                            transacciones_dia = [t for t in transacciones_mes if t[0].day == dia]
                            for _, cantidad in transacciones_dia:
                                balance_acumulado += cantidad
                            balance_por_dia[dia] = balance_acumulado
        
                        for dia in range(1, dia_actual + 1):
                            daily_labels.append(str(dia))
                            daily_data.append(round(balance_por_dia.get(dia, balance_inicio_mes), 2))
        
            # Crear PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
        
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
            )
            story.append(Paragraph(f'Reporte de Gráficos - Plan: {plan.nombre}', title_style))
            story.append(Spacer(1, 12))
        
            # Información del período
            if selected_month:
                periodo = f"Período: {selected_month}"
            else:
                periodo = f"Año: {selected_year}"
            story.append(Paragraph(periodo, styles['Normal']))
            story.append(Spacer(1, 20))
        
            # Crear gráficos con matplotlib
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
        
            # Gráfico diario
            if daily_labels:
                ax1.plot(daily_labels, daily_data, marker='o', color='blue')
                ax1.set_title('Balance Diario del Último Mes')
                ax1.set_xlabel('Día del Mes')
                ax1.set_ylabel('Balance ($)')
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No hay datos disponibles', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Balance Diario del Último Mes')
        
            # Gráfico mensual
            bars = ax2.bar(monthly_labels, monthly_data, color=['green' if x >= 0 else 'red' for x in monthly_data])
            ax2.set_title(f'Resumen de {selected_year}')
            ax2.set_xlabel('Mes')
            ax2.set_ylabel('Dinero Ganado/Perdido ($)')
            ax2.grid(True, alpha=0.3)
        
            # Ajustar layout
            plt.tight_layout()
        
            # Convertir a imagen para PDF
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
        
            # Agregar imagen al PDF
            img = Image(img_buffer)
            img.drawHeight = 6 * inch
            img.drawWidth = 7 * inch
            story.append(img)
        
            # Generar fecha del reporte
            story.append(Spacer(1, 20))
            story.append(Paragraph(f'Reporte generado el: {hoy.strftime("%d/%m/%Y")}', styles['Normal']))
        
            # Construir PDF
            doc.build(story)
        
            # Preparar respuesta
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_graficos_{plan.nombre}_{hoy.strftime("%Y%m%d")}.pdf"'
            return response


@login_required
def descargar_pdf_historial(request, plan_id, tipo):
    """Genera y descarga un PDF con el historial de ingresos o gastos."""
    plan, es_miembro = verificar_membresia(request, plan_id)
    if not es_miembro:
        return HttpResponse('No autorizado', status=403)

    if tipo not in ['ingresos', 'gastos']:
        return HttpResponse('Tipo inválido', status=400)

    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    import io

    dinero_obj = get_object_or_404(Dinero, plan=plan)

    if tipo == 'ingresos':
        transacciones = Ingreso.objects.filter(dinero=dinero_obj).select_related('user').order_by('-fecha_guardado')
        titulo = f'Historial de Ingresos - Plan: {plan.nombre}'
    else:
        transacciones = Gasto.objects.filter(dinero=dinero_obj).select_related('user').order_by('-fecha_guardado')
        titulo = f'Historial de Gastos - Plan: {plan.nombre}'

    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
    )
    story.append(Paragraph(titulo, title_style))
    story.append(Spacer(1, 12))

    # Fecha del reporte
    from django.utils import timezone
    hoy = timezone.now().date()
    story.append(Paragraph(f'Reporte generado el: {hoy.strftime("%d/%m/%Y")}', styles['Normal']))
    story.append(Spacer(1, 20))

    if transacciones:
        # Crear tabla de datos
        data = [['Nombre', 'Descripción', 'Tipo', 'Usuario', 'Cantidad', 'Fecha']]

        for transaccion in transacciones:
            if tipo == 'ingresos':
                tipo_display = transaccion.get_tipo_ingreso_display()
                cantidad = f'+${transaccion.cantidad:.2f}'
            else:
                tipo_display = transaccion.get_tipo_gasto_display()
                cantidad = f'-${transaccion.cantidad:.2f}'

            data.append([
                transaccion.nombre,
                transaccion.descripcion or 'Sin descripción',
                tipo_display,
                transaccion.user.username,
                cantidad,
                transaccion.fecha_guardado.strftime('%d/%m/%Y %H:%M')
            ])

        # Crear tabla
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
    else:
        story.append(Paragraph(f'No hay {tipo} registrados.', styles['Normal']))

    # Construir PDF
    doc.build(story)

    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="historial_{tipo}_{plan.nombre}_{hoy.strftime("%Y%m%d")}.pdf"'
    return response


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

from django.shortcuts import render, get_object_or_404, redirect
from .models import Plan, Suscripcion, Ingreso, Gasto
from .forms import IngresoForm, GastoForm

def Menu_plan(request, plan_id):
    # Aquí sí, usa el plan_id para obtener el plan correcto
    plan = get_object_or_404(Plan, pk=plan_id)
    
    context = {
        'plan': plan,
    }
    return render(request, 'menu_plan.html', context)

def estadisticas(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    ingresos_totales = sum(ingreso.cantidad for ingreso in plan.ingresos.all())
    gastos_totales = sum(gasto.cantidad for gasto in plan.gastos.all())
    ganancia_neta = ingresos_totales - gastos_totales

    context = {
        'plan': plan,
        'ganancia_neta': ganancia_neta,
        'ingresos_totales': ingresos_totales,
        'gastos_totales': gastos_totales,
    }
    return render(request, 'estadisticas.html', context)


def ingresos(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)

    if request.method == 'POST':
        form = IngresoForm(request.POST)
        if form.is_valid():
            nuevo_ingreso = form.save(commit=False)
            nuevo_ingreso.plan = plan
            nuevo_ingreso.save()
            return redirect('ingresos', plan_id=plan.id)
    else:
        form = IngresoForm()

    ingresos_del_plan = plan.ingresos.all()
    context = {
        'plan': plan,
        'form': form,
        'ingresos_del_plan': ingresos_del_plan,
    }
    return render(request, 'ingresos.html', context)

def gastos(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)

    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            nuevo_gasto = form.save(commit=False)
            nuevo_gasto.plan = plan
            nuevo_gasto.save()
            return redirect('gastos', plan_id=plan.id)
    else:
        form = GastoForm()

    gastos_del_plan = plan.gastos.all()
    context = {
        'plan': plan,
        'form': form,
        'gastos_del_plan': gastos_del_plan,
    }
    return render(request, 'gastos.html', context)
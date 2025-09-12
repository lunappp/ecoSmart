# Planes_app/views.py

from django.shortcuts import render, get_object_or_404
from .models import Plan

def Menu_plan(request, plan_id):
    # Aquí sí, usa el plan_id para obtener el plan correcto
    plan = get_object_or_404(Plan, pk=plan_id)
    
    context = {
        'plan': plan,
    }
    return render(request, 'menu_plan.html', context)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
from Planes_app.models import Plan, Suscripcion, Dinero, Ingreso, Gasto, Objetivo, Tarea
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import os
import csv

@login_required
def chatbot_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    # Verificar que el usuario tenga acceso al plan
    if not (plan.creador == request.user or plan.suscripciones.filter(usuario=request.user).exists()):
        return redirect('Dashboard')
    messages = Message.objects.filter(user=request.user, plan=plan).order_by('timestamp')
    return render(request, 'chatbot/chatbot.html', {'messages': messages, 'plan': plan})

@login_required
def send_message(request, plan_id):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            plan = get_object_or_404(Plan, id=plan_id)
            # Verificar acceso
            if not (plan.creador == request.user or plan.suscripciones.filter(usuario=request.user).exists()):
                return JsonResponse({'error': 'No access'}, status=403)
            # Get AI response
            bot_response = get_ai_response(user_message, request.user, plan)
            # Save to database
            Message.objects.create(
                user=request.user,
                plan=plan,
                user_message=user_message,
                bot_response=bot_response
            )
            return JsonResponse({'response': bot_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

chatbot = ChatBot('EcoSmartBotV2')

# Entrenar con conocimientos desde CSV
trainer = ListTrainer(chatbot)

# Cargar datos desde CSV
training_data = []
with open('finanzas_dataset.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        training_data.extend([row['pregunta'], row['respuesta']])

trainer.train(training_data)

def get_ai_response(message, user, plan):
    message_lower = message.lower()
    
    # Lógica para revisar el plan actual
    if 'plan' in message_lower or 'planes' in message_lower:
        response = f"Plan actual: {plan.nombre} - {plan.descripcion}\n"
        response += "Otros planes:\n"
        otros_planes = (Plan.objects.filter(creador=user) | Plan.objects.filter(suscripciones__usuario=user)).exclude(id=plan.id).distinct()
        for p in otros_planes:
            response += f"- {p.nombre}: {p.descripcion}\n"
        return response
    
    # Lógica para gastos del plan
    if 'gasto' in message_lower or 'gastos' in message_lower:
        gastos = Gasto.objects.filter(dinero__plan=plan).order_by('-fecha_guardado')[:5]
        if gastos.exists():
            response = f"Análisis de gastos del plan '{plan.nombre}':\n"
            for gasto in gastos:
                analisis = analizar_gasto(gasto)
                response += f"- {gasto.nombre}: ${gasto.cantidad} ({gasto.tipo_gasto})\n  Análisis: {analisis}\n"
            return response
        else:
            return f"No hay gastos registrados en el plan '{plan.nombre}'."
    
    # Lógica para ingresos del plan
    if 'ingreso' in message_lower or 'ingresos' in message_lower:
        ingresos = Ingreso.objects.filter(dinero__plan=plan).order_by('-fecha_guardado')[:5]
        if ingresos.exists():
            response = f"Ingresos del plan '{plan.nombre}':\n"
            for ingreso in ingresos:
                response += f"- {ingreso.nombre}: ${ingreso.cantidad} ({ingreso.tipo_ingreso})\n"
            return response
        else:
            return f"No hay ingresos registrados en el plan '{plan.nombre}'."
    
    # Lógica para objetivos del plan
    if 'objetivo' in message_lower or 'objetivos' in message_lower:
        objetivos = Objetivo.objects.filter(plan=plan)
        if objetivos.exists():
            response = f"Objetivos del plan '{plan.nombre}':\n"
            for obj in objetivos:
                progreso = (obj.monto_actual / obj.monto_necesario) * 100 if obj.monto_necesario > 0 else 0
                response += f"- {obj.nombre}: ${obj.monto_actual}/${obj.monto_necesario} ({progreso:.1f}%)\n"
            return response
        else:
            return f"No hay objetivos registrados en el plan '{plan.nombre}'."
    
    # Lógica para tareas del plan
    if 'tarea' in message_lower or 'tareas' in message_lower:
        tareas = Tarea.objects.filter(plan=plan)
        if tareas.exists():
            response = f"Tareas del plan '{plan.nombre}':\n"
            for tarea in tareas:
                response += f"- {tarea.nombre}: {tarea.estado} (Fecha: {tarea.fecha_a_completar})\n"
            return response
        else:
            return f"No hay tareas registradas en el plan '{plan.nombre}'."
    
    # Lógica para saldo
    if 'saldo' in message_lower or 'cuánto tengo' in message_lower or 'dinero' in message_lower:
        try:
            dinero = plan.dinero
            total_ingresos = sum(i.cantidad for i in dinero.ingresos.all())
            total_gastos = sum(g.cantidad for g in dinero.gastos.all())
            saldo = total_ingresos - total_gastos
            return f"En el plan '{plan.nombre}', tienes un saldo de ${saldo:.2f} (Ingresos: ${total_ingresos:.2f}, Gastos: ${total_gastos:.2f})."
        except:
            return "No hay información financiera registrada en este plan."

    # Lógica para consejos del plan
    if 'consejo' in message_lower or 'ayuda' in message_lower or 'recomendacion' in message_lower:
        return generar_consejos(user, plan)

    # Respuesta por defecto con ChatterBot si tiene alta confianza
    try:
        response = chatbot.get_response(message)
        if response.confidence > 0.8:  # Solo responder si confianza muy alta
            return str(response)
        else:
            return "Lo siento, no entendí tu consulta. Puedes preguntarme sobre tu plan, gastos, ingresos, objetivos, tareas, saldo o pedir consejos."
    except Exception as e:
        return "Lo siento, no entendí tu consulta. Puedes preguntarme sobre tu plan, gastos, ingresos, objetivos, tareas, saldo o pedir consejos."

def analizar_gasto(gasto):
    nombre = gasto.nombre.lower()
    descripcion = (gasto.descripcion or "").lower()
    tipo = gasto.tipo_gasto.lower()
    cantidad = gasto.cantidad

    # Análisis basado en tipo y nombre
    if tipo == 'alimentacion':
        if 'restaurante' in nombre or 'comida rapida' in nombre:
            return "Gasto en alimentación fuera de casa. Considera cocinar en casa para ahorrar."
        else:
            return "Gasto esencial en alimentación. Mantén un presupuesto semanal."

    elif tipo == 'transporte':
        if 'taxi' in nombre or 'uber' in nombre:
            return "Gasto en transporte privado. Usa transporte público o bicicleta cuando sea posible."
        else:
            return "Gasto en transporte. Revisa si puedes optimizar rutas o usar alternativas económicas."

    elif tipo == 'entretenimiento':
        if cantidad > 100:  # Ejemplo de umbral
            return "Gasto alto en entretenimiento. Evalúa si es necesario o busca alternativas gratuitas."
        else:
            return "Gasto moderado en entretenimiento. Es importante para el bienestar, pero mantén el equilibrio."

    elif tipo == 'servicios':
        return "Gasto en servicios básicos. Es esencial, pero compara proveedores para mejores precios."

    elif tipo == 'alquiler':
        return "Gasto en vivienda. Si supera el 30% de ingresos, considera opciones más económicas."

    else:
        # Análisis general basado en palabras clave
        if 'cafe' in nombre or 'starbucks' in nombre:
            return "Gasto en café. Pequeños gastos diarios pueden sumar mucho; considera preparar en casa."
        elif 'cigarrillos' in nombre or 'tabaco' in nombre:
            return "Gasto en tabaco. Considera dejarlo para mejorar salud financiera y física."
        elif 'juegos' in nombre or 'videojuegos' in nombre:
            return "Gasto en entretenimiento digital. Limita compras impulsivas."
        elif 'ropa' in nombre or 'zapatos' in nombre:
            return "Gasto en vestimenta. Revisa si es necesario o busca ofertas."
        else:
            return "Gasto clasificado como 'otro'. Revisa si es esencial o puede reducirse."

def generar_consejos(user, plan):
    consejos = []

    # Obtener datos del plan
    try:
        dinero = plan.dinero
        ingresos = dinero.ingresos.all()
        gastos = dinero.gastos.all()
    except:
        ingresos = []
        gastos = []

    objetivos = plan.objetivos.all()
    tareas = plan.tareas.all()

    total_ingresos = sum(i.cantidad for i in ingresos)
    total_gastos = sum(g.cantidad for g in gastos)

    if total_ingresos > 0 and total_gastos > 0:
        ahorro = total_ingresos - total_gastos
        if ahorro > 0:
            consejos.append(f"¡Excelente! En el plan '{plan.nombre}' estás ahorrando ${ahorro}. Considera invertir en objetivos o reducir gastos innecesarios.")
        else:
            consejos.append(f"En el plan '{plan.nombre}' estás gastando más de lo que ingresas (${-ahorro} de déficit). Revisa tus gastos y busca formas de aumentar ingresos.")

    if objetivos.exists():
        for obj in objetivos:
            if obj.estado == 'pendiente' and obj.monto_actual < obj.monto_necesario:
                restante = obj.monto_necesario - obj.monto_actual
                consejos.append(f"Para el objetivo '{obj.nombre}' en '{plan.nombre}', te faltan ${restante}. Planea pagos mensuales para alcanzarlo.")

    tareas_pendientes = tareas.filter(estado='pendiente')
    if tareas_pendientes.exists():
        consejos.append(f"En el plan '{plan.nombre}' tienes {tareas_pendientes.count()} tareas pendientes. Prioriza las más urgentes.")

    if not consejos:
        consejos.append("Mantén un registro constante de tus finanzas en este plan. Revisa tus gastos mensualmente y ajusta tus objetivos.")

    return f"Consejos basados en el plan '{plan.nombre}':\n" + "\n".join(f"- {c}" for c in consejos)
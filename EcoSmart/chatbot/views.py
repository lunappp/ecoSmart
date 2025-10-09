from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
from Planes_app.models import Plan, Suscripcion, Dinero, Ingreso, Gasto, Objetivo, Tarea
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import os

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

chatbot = ChatBot('EcoSmartBot')

# Entrenar con conocimientos básicos sobre finanzas
trainer = ListTrainer(chatbot)
trainer.train([
    "Hola", "¡Hola! Soy el asistente de EcoSmart. ¿En qué puedo ayudarte con tus finanzas?",
    "Hola", "¡Hola! ¿Cómo estás? ¿Necesitas ayuda con tu plan financiero?",
    "¿Qué es EcoSmart?", "EcoSmart es una aplicación para gestionar tus finanzas personales, planes de ahorro y gastos.",
    "¿Qué hace EcoSmart?", "EcoSmart te ayuda a registrar ingresos, gastos, objetivos y tareas para mejorar tu salud financiera.",
    "¿Cómo ahorro dinero?", "Para ahorrar, registra tus ingresos y gastos, establece objetivos y revisa tus hábitos de consumo.",
    "¿Cómo ahorrar más?", "Reduce gastos innecesarios, busca ingresos extra y automatiza transferencias a una cuenta de ahorro.",
    "¿Qué es un presupuesto?", "Un presupuesto es un plan que detalla tus ingresos y gastos para controlar tus finanzas.",
    "¿Cómo hacer un presupuesto?", "Suma tus ingresos, lista tus gastos fijos y variables, y asigna porcentajes a categorías como 50% necesidades, 30% deseos, 20% ahorro.",
    "¿Cómo invertir?", "Invertir implica riesgo. Empieza con educación financiera y considera opciones seguras como fondos indexados.",
    "¿Qué inversiones recomiendas?", "Para principiantes, ETFs de bajo costo o cuentas de ahorro de alto rendimiento. Consulta a un asesor financiero.",
    "¿Qué es deuda?", "Deuda es dinero que debes. Trata de evitar deudas de alto interés y paga lo que puedas.",
    "¿Cómo manejar deudas?", "Prioriza pagar deudas de alto interés primero. Considera consolidación o negociación con acreedores.",
    "¿Qué es un objetivo financiero?", "Un objetivo financiero es una meta monetaria, como ahorrar para una casa o pagar deudas.",
    "¿Cómo establecer objetivos?", "Hazlos SMART: Específicos, Medibles, Alcanzables, Relevantes y con Tiempo definido.",
    "¿Qué es un ingreso?", "Ingreso es dinero que recibes, como salario, inversiones o regalos.",
    "¿Qué es un gasto?", "Gasto es dinero que sales, como comida, alquiler o entretenimiento.",
    "¿Cómo controlar gastos?", "Registra todos los gastos, categorízalos y compara con tu presupuesto mensual.",
    "¿Qué es ahorro?", "Ahorro es dinero que guardas para emergencias o metas futuras.",
    "¿Cuánto debo ahorrar?", "Idealmente, 3-6 meses de gastos en emergencias, y 20% de ingresos para metas.",
    "¿Qué es una tarea financiera?", "Una tarea financiera es una acción pendiente, como pagar una factura o revisar inversiones.",
    "¿Cómo gestionar tareas?", "Usa listas, establece fechas límite y prioriza las importantes.",
    "Adiós", "¡Hasta luego! Recuerda revisar tus finanzas regularmente.",
    "Gracias", "¡De nada! Estoy aquí para ayudar con tus finanzas.",
])

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
            response = f"Gastos del plan '{plan.nombre}':\n"
            for gasto in gastos:
                response += f"- {gasto.nombre}: ${gasto.cantidad} ({gasto.tipo_gasto})\n"
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

    # Respuesta por defecto con ChatterBot
    try:
        response = chatbot.get_response(message)
        return str(response)
    except Exception as e:
        return f"Error: {str(e)}"

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
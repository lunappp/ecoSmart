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

chatbot = ChatBot('EcoSmartBotV2')

# Entrenar con conocimientos avanzados sobre finanzas
trainer = ListTrainer(chatbot)
trainer.train([
    # Saludos y despedidas
    "Hola", "¡Hola! Soy EcoBot, tu asistente financiero de EcoSmart. ¿Cómo puedo ayudarte hoy?",
    "Hola", "¡Hola! ¿Qué tal? ¿Necesitas consejos sobre tus finanzas?",
    "Buenos días", "¡Buenos días! ¿Listo para revisar tus finanzas?",
    "Buenas tardes", "¡Buenas tardes! ¿En qué puedo asistirte con tu plan financiero?",
    "Buenas noches", "¡Buenas noches! ¿Quieres un resumen de tu día financiero?",
    "Adiós", "¡Hasta luego! No olvides registrar tus transacciones.",
    "Chao", "¡Chao! Recuerda ahorrar para el futuro.",
    "Gracias", "¡De nada! Estoy aquí para ayudarte con tus finanzas.",
    "Gracias por tu ayuda", "¡Es un placer! ¿Algo más en lo que pueda asistirte?",
    "¿Cómo estás?", "¡Estoy bien, gracias! ¿Y tú?",
    "¿Qué tal?", "¡Todo bien! ¿Qué hay de ti?",
    "Bien y tú?", "¡Excelente! ¿En qué puedo ayudarte hoy?",
    "Bien, gracias", "¡Me alegra! ¿Necesitas ayuda con tus finanzas?",
    "Todo bien", "¡Genial! ¿Quieres revisar tu plan financiero?",

    # Preguntas sobre EcoSmart
    "¿Qué es EcoSmart?", "EcoSmart es una plataforma integral para gestionar finanzas personales, con planes, objetivos y seguimiento de gastos.",
    "¿Qué hace EcoSmart?", "EcoSmart te permite crear planes financieros, registrar ingresos y gastos, establecer objetivos y gestionar tareas.",
    "¿Cómo funciona EcoSmart?", "Registra tus datos financieros, crea planes personalizados y recibe consejos basados en tu información.",

    # Consejos de ahorro
    "¿Cómo ahorro dinero?", "Registra todos tus gastos, identifica áreas de mejora, establece un presupuesto y ahorra automáticamente.",
    "¿Cómo ahorrar más?", "Corta suscripciones innecesarias, cocina en casa, busca ingresos extra y establece metas de ahorro.",
    "¿Cuánto debo ahorrar?", "Recomiendo el 20% de tus ingresos para ahorro, más 3-6 meses de gastos para emergencias.",
    "¿Cómo empezar a ahorrar?", "Comienza con pequeños cambios: registra gastos diarios, establece un presupuesto y ahorra $10 al día.",

    # Presupuestos
    "¿Qué es un presupuesto?", "Un presupuesto es un plan financiero que asigna tus ingresos a gastos, ahorro e inversiones.",
    "¿Cómo hacer un presupuesto?", "1. Calcula ingresos totales. 2. Lista gastos fijos. 3. Asigna porcentajes: 50% necesidades, 30% deseos, 20% ahorro.",
    "¿Cómo mantener un presupuesto?", "Revisa semanalmente, ajusta según cambios y usa apps como EcoSmart para seguimiento.",

    # Inversiones
    "¿Cómo invertir?", "Educa primero, diversifica, invierte a largo plazo y considera ETFs o fondos indexados para principiantes.",
    "¿Qué inversiones recomiendas?", "Para principiantes: ETFs de bajo costo, cuentas de ahorro de alto rendimiento o fondos mutuos.",
    "¿Es seguro invertir?", "La inversión implica riesgo, pero diversificar y educarte reduce riesgos. Nunca inviertas dinero que necesites inmediatamente.",
    "¿Cuándo empezar a invertir?", "Tan pronto como tengas un fondo de emergencia. Empieza pequeño y aprende continuamente.",

    # Deudas
    "¿Qué es deuda buena?", "Deuda buena es aquella que genera valor, como hipoteca para casa o educación que aumenta ingresos.",
    "¿Qué es deuda mala?", "Deuda mala es de alto interés como tarjetas de crédito para compras innecesarias.",
    "¿Cómo pagar deudas?", "Usa método avalancha: paga primero deudas de alto interés, luego consolida si es necesario.",
    "¿Cómo evitar deudas?", "Vive por debajo de tus medios, ahorra antes de gastar y usa efectivo en lugar de crédito.",

    # Objetivos financieros
    "¿Qué es un objetivo financiero?", "Una meta monetaria específica, como ahorrar $10,000 para vacaciones o pagar una deuda.",
    "¿Cómo establecer objetivos?", "Usa método SMART: Específico, Medible, Alcanzable, Relevante y con Tiempo definido.",
    "¿Cómo alcanzar objetivos?", "Divide en pasos pequeños, automatiza ahorros y revisa progreso mensualmente.",

    # Ingresos y gastos
    "¿Qué es ingreso pasivo?", "Ingreso que se genera con poco esfuerzo continuo, como alquileres o dividendos.",
    "¿Cómo aumentar ingresos?", "Busca trabajos extra, vende items, invierte en habilidades o inicia un negocio pequeño.",
    "¿Cómo controlar gastos?", "Categoriza gastos, identifica fugas y establece límites mensuales por categoría.",
    "¿Qué gastos son necesarios?", "Alquiler/vivienda, comida, transporte básico, seguros y pagos mínimos de deudas.",

    # Emergencias
    "¿Por qué necesito fondo de emergencia?", "Cubre gastos inesperados como reparaciones o pérdida de trabajo, evita deudas.",
    "¿Cuánto en fondo de emergencia?", "3-6 meses de gastos esenciales. Empieza con $1,000 y construye gradualmente.",

    # Crédito
    "¿Cómo mejorar mi crédito?", "Paga facturas a tiempo, reduce deuda, evita nuevas solicitudes de crédito y revisa reporte anual.",
    "¿Qué es puntaje de crédito?", "Número que mide confiabilidad para préstamos. Mayor puntaje = mejores tasas.",

    # Impuestos
    "¿Cómo ahorrar en impuestos?", "Maximiza contribuciones a 401(k), deduce gastos legítimos y planifica con anticipación.",
    "¿Qué deducciones puedo reclamar?", "Hipoteca, intereses estudiantiles, donaciones caritativas y gastos médicos.",

    # Retiro
    "¿Cómo planificar retiro?", "Calcula cuánto necesitas, contribuye regularmente a cuentas de retiro y diversifica inversiones.",
    "¿Cuánto necesito para retiro?", "Regla general: 25x gastos anuales. Usa calculadoras en línea para estimar.",

    # Consejos generales
    "¿Cómo mejorar mi situación financiera?", "Registra todo, crea presupuesto, paga deudas, ahorra automáticamente y educa continuamente.",
    "¿Cuál es el secreto de la riqueza?", "Gasta menos de lo que ganas, invierte la diferencia y sé paciente.",
    "¿Cómo enseñar finanzas a niños?", "Usa juegos, establece chores con paga, enseña presupuesto y da ejemplo.",

    # Conversación social y empatía
    "Estoy estresado", "Entiendo que las finanzas pueden ser estresantes. ¿Quieres hablar de lo que te preocupa?",
    "Estoy feliz", "¡Me alegra oír eso! ¿Qué te hace feliz hoy?",
    "Estoy triste", "Lo siento mucho. ¿Hay algo en lo que pueda ayudarte para mejorar tu día?",
    "Tengo miedo", "Es normal tener miedos financieros. Hablemos de cómo manejarlos.",
    "Estoy motivado", "¡Excelente actitud! ¿Qué te motiva a mejorar tus finanzas?",
    "¿Cómo estás?", "Estoy bien, gracias por preguntar. ¿Y tú?",
    "¿Qué haces?", "Ayudo a las personas con sus finanzas. ¿En qué puedo asistirte?",
    "Cuéntame de ti", "Soy un asistente de IA especializado en finanzas. Mi objetivo es ayudarte a alcanzar tus metas económicas.",
    "Háblame de algo", "Puedo contarte consejos financieros o responder preguntas sobre ahorro, inversiones o presupuestos.",
    "Dime un chiste", "Por qué el matemático no podía dormir? Porque tenía demasiados problemas.",
    "Háblame del clima", "No tengo acceso al clima actual, pero puedo ayudarte con finanzas. ¿Qué tal si revisamos tu presupuesto?",
    "Estoy aburrido", "¡Vamos a hacer algo productivo! ¿Quieres que te dé consejos para ahorrar dinero?",
    "Te quiero", "¡Gracias! Yo también aprecio nuestra conversación. ¿Cómo puedo ayudarte con tus finanzas?",
    "Eres genial", "¡Gracias! Me esfuerzo por ser útil. ¿Qué más puedo hacer por ti?",
    "Eres malo", "Lo siento si te hice sentir así. ¿Cómo puedo mejorar mi ayuda?",
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

    # Respuesta por defecto con ChatterBot si tiene alta confianza
    try:
        response = chatbot.get_response(message)
        if response.confidence > 0.8:  # Solo responder si confianza muy alta
            return str(response)
        else:
            return "Lo siento, no entendí tu consulta. Puedes preguntarme sobre tu plan, gastos, ingresos, objetivos, tareas, saldo o pedir consejos."
    except Exception as e:
        return "Lo siento, no entendí tu consulta. Puedes preguntarme sobre tu plan, gastos, ingresos, objetivos, tareas, saldo o pedir consejos."

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
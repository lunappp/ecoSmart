from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
import re
import os
import django
from django.conf import settings

# Configurar Django para las custom actions
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EcoSmart.settings')
django.setup()

from Planes_app.models import Plan, Dinero, Ingreso, Gasto, Objetivo

@login_required
def chatbot_view(request, plan_id=None):
    messages = Message.objects.filter(user=request.user).order_by('timestamp')
    context = {'messages': messages}
    if plan_id:
        context['plan_id'] = plan_id
    return render(request, 'chatbot/chatbot.html', context)

@login_required
def send_message(request, plan_id=None):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Get AI response using simple NLP logic
            bot_response = get_simple_response(user_message.lower(), plan_id)
            # Save to database
            Message.objects.create(
                user=request.user,
                user_message=user_message,
                bot_response=bot_response
            )
            return JsonResponse({'response': bot_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_simple_response(message, plan_id=None):
    """
    Simple NLP logic to respond to user messages based on keywords
    Each plan has its own AI that analyzes specific plan data
    """

    # Get plan data if plan_id is provided
    plan_data = None
    if plan_id:
        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)
            plan_data = {
                'plan': plan,
                'dinero': dinero,
                'ingresos': dinero.ingreso_total,
                'gastos': dinero.gasto_total,
                'balance': dinero.ingreso_total - dinero.gasto_total,
                'objetivos': list(plan.objetivos.all()),
                'tareas': list(plan.tareas.all())
            }
        except Exception as e:
            return f"Error al acceder a los datos del plan: {str(e)}"

    # Greeting patterns
    if any(word in message for word in ['hola', 'hello', 'hi', 'hey', 'buenos dias', 'buenas tardes']):
        if plan_data:
            return f"¡Hola! Soy el asistente IA de tu plan '{plan_data['plan'].nombre}'. ¿En qué puedo ayudarte hoy?"
        return "¡Hola! Soy tu asistente de EcoSmart. ¿En qué puedo ayudarte hoy?"

    # Goodbye patterns
    if any(word in message for word in ['adios', 'bye', 'chau', 'hasta luego', 'nos vemos']):
        return "¡Hasta luego! Que tengas un excelente día."

    # Plan-specific data requests
    if plan_data:
        # Summary/Resumen requests
        if any(word in message for word in ['resumen', 'summary', 'estado', 'status', 'como va', 'how is it going']):
            return get_plan_summary(plan_data)

        # Detailed data analysis
        if any(word in message for word in ['datos', 'data', 'informacion', 'info', 'detalles']):
            return get_detailed_plan_data(plan_data)

        # Budget analysis and advice
        if any(word in message for word in ['presupuesto', 'budget', 'analizar presupuesto', 'budget analysis']):
            return get_budget_analysis(plan_data)

        # Expense breakdown
        if any(word in message for word in ['gastos', 'expenses', 'desglose gastos', 'expense breakdown']):
            return get_expense_breakdown(plan_data)

        # Savings analysis
        if any(word in message for word in ['ahorros', 'savings', 'ahorro', 'analizar ahorros']):
            return get_savings_analysis(plan_data)

        # Goals progress
        if any(word in message for word in ['metas', 'goals', 'objetivos', 'progreso metas']):
            return get_goals_progress(plan_data)

        # Tasks/To-do list
        if any(word in message for word in ['tareas', 'tasks', 'pendientes', 'to do']):
            return get_tasks_summary(plan_data)

        # Investment recommendations based on plan data
        if any(word in message for word in ['invertir', 'invest', 'inversiones', 'investment']):
            return get_investment_recommendations(plan_data)

        # Personalized advice
        if any(word in message for word in ['consejo', 'advice', 'recomendacion', 'sugerencia']):
            return get_personalized_advice(plan_data)

        # Financial education
        if any(word in message for word in ['educacion', 'education', 'aprender', 'learn', 'enseñame']):
            return get_financial_education(plan_data)

        # Market insights
        if any(word in message for word in ['mercado', 'market', 'tendencias', 'trends', 'analisis mercado']):
            return get_market_insights(plan_data)

        # Risk assessment
        if any(word in message for word in ['riesgo', 'risk', 'tolerancia riesgo', 'perfil inversion']):
            return get_risk_assessment(plan_data)

        # Tax optimization
        if any(word in message for word in ['impuestos', 'tax', 'fiscal', 'taxes', 'optimizar impuestos']):
            return get_tax_optimization(plan_data)

        # Estate planning
        if any(word in message for word in ['herencia', 'estate', 'patrimonio', 'sucesion', 'planificacion']):
            return get_estate_planning(plan_data)

    # General economy questions (when no specific plan)
    if any(word in message for word in ['economia', 'economy', 'que es economia', 'what is economy']):
        return "La economía es el estudio de cómo las personas y sociedades administran sus recursos limitados. En EcoSmart, te ayudamos a gestionar tu presupuesto, ahorros e inversiones."

    # General budget questions
    if any(word in message for word in ['presupuesto', 'budget', 'como hacer presupuesto', 'how to budget']):
        return "Para un buen presupuesto: 50% para necesidades, 30% para deseos, 20% para ahorros e inversiones."

    # General savings questions
    if any(word in message for word in ['ahorrar', 'save', 'savings', 'ahorro', 'como ahorrar']):
        return "Recomiendo ahorrar al menos el 20% de tus ingresos. Usa cuentas de ahorro de alto rendimiento."

    # General investment questions
    if any(word in message for word in ['invertir', 'invest', 'inversiones', 'como invertir']):
        return "Diversifica tus inversiones. Considera fondos indexados para principiantes."

    # General expense questions
    if any(word in message for word in ['gastos', 'expenses', 'controlar gastos', 'reducir gastos']):
        return "Analicemos tus gastos. ¿Qué categoría consumes más?"

    # General income questions
    if any(word in message for word in ['ingresos', 'income', 'aumentar ingresos', 'ganar mas']):
        return "Para optimizar ingresos: busca fuentes adicionales, negocia aumentos, invierte en educación."

    # General goal questions
    if any(word in message for word in ['metas', 'goals', 'objetivos', 'establecer metas']):
        return "Establece metas SMART: Específicas, Medibles, Alcanzables, Relevantes, con Tiempo definido."

    # General tips questions
    if any(word in message for word in ['consejos', 'tips', 'advice', 'recomendaciones']):
        return "Consejo general: Vive por debajo de tus posibilidades y construye riqueza gradualmente."

    # Bot identity questions
    if any(word in message for word in ['bot', 'robot', 'ai', 'artificial', 'eres un bot']):
        if plan_data:
            return f"Soy la IA personal de tu plan '{plan_data['plan'].nombre}', creada por EcoSmart para ayudarte con tus finanzas específicas."
        return "Soy un bot creado por EcoSmart para ayudarte con tus finanzas. ¡Estoy aquí para asistirte!"

    # Mood responses
    if any(word in message for word in ['bien', 'good', 'great', 'excelente', 'perfecto']):
        return "¡Me alegra oír eso! ¿En qué más puedo ayudarte?"

    if any(word in message for word in ['mal', 'bad', 'triste', 'sad', 'horrible']):
        return "Lamento oír eso. ¿Hay algo en específico en lo que pueda ayudarte con tus finanzas?"

    # Default response
    if plan_data:
        return f"Lo siento, no entendí tu mensaje. Como IA de tu plan '{plan_data['plan'].nombre}', puedo ayudarte con:\n\n📊 **Análisis Financiero:**\n• Resumen financiero completo\n• Análisis detallado de presupuesto\n• Desglose de gastos por categorías\n• Análisis de ahorros y recomendaciones\n\n🎯 **Metas y Tareas:**\n• Progreso de tus objetivos\n• Lista de tareas pendientes\n\n💡 **Consejos Avanzados:**\n• Recomendaciones de inversión personalizadas\n• Consejos financieros personalizados\n• Educación financiera completa\n• Análisis de mercado y tendencias\n• Evaluación de tolerancia al riesgo\n• Optimización fiscal\n• Planificación patrimonial\n\n¿Qué te gustaría saber?"
    return "Lo siento, no entendí tu mensaje. Puedes preguntarme sobre economía, presupuesto, ahorros, inversiones, gastos, ingresos o metas financieras. Si tienes un plan específico, puedo darte consejos personalizados basados en tus datos."


def get_plan_summary(plan_data):
    """Generate a comprehensive summary of the plan's financial status"""
    plan = plan_data['plan']
    ingresos = plan_data['ingresos']
    gastos = plan_data['gastos']
    balance = plan_data['balance']
    objetivos = plan_data['objetivos']
    tareas = plan_data['tareas']

    summary = f"📊 **Resumen Financiero del Plan '{plan.nombre}'**\n\n"

    # Financial overview
    summary += f"💰 **Estado Financiero:**\n"
    summary += f"• Ingresos totales: ${ingresos:,.0f}\n"
    summary += f"• Gastos totales: ${gastos:,.0f}\n"
    summary += f"• Balance actual: ${balance:,.0f}\n"

    if ingresos > 0:
        ratio_gastos = (gastos / ingresos) * 100
        ratio_ahorro = ((ingresos - gastos) / ingresos) * 100
        summary += f"• Ratio gastos/ingresos: {ratio_gastos:.1f}%\n"
        summary += f"• Ratio ahorro: {ratio_ahorro:.1f}%\n"

    # Goals progress
    if objetivos:
        summary += f"\n🎯 **Metas ({len(objetivos)}):**\n"
        for obj in objetivos[:3]:  # Show top 3 goals
            progreso = (obj.monto_actual / obj.monto_necesario) * 100 if obj.monto_necesario > 0 else 0
            status = "✅ Completada" if obj.estado == 'completado' else f"🔄 {progreso:.1f}% completado"
            summary += f"• {obj.nombre}: ${obj.monto_actual:,.0f} / ${obj.monto_necesario:,.0f} ({status})\n"

    # Tasks summary
    if tareas:
        pendientes = [t for t in tareas if t.estado != 'completada']
        completadas = [t for t in tareas if t.estado == 'completada']
        summary += f"\n📝 **Tareas:**\n"
        summary += f"• Pendientes: {len(pendientes)}\n"
        summary += f"• Completadas: {len(completadas)}\n"

    # Quick advice
    if balance < 0:
        summary += f"\n⚠️ **Alerta:** Tu balance es negativo. Considera reducir gastos o aumentar ingresos."
    elif balance > ingresos * 0.2:
        summary += f"\n✅ **Excelente:** Estás ahorrando más del 20% recomendado."
    else:
        summary += f"\n💡 **Consejo:** Podrías aumentar tus ahorros para tener una mejor reserva financiera."

    return summary


def get_detailed_plan_data(plan_data):
    """Provide detailed financial data breakdown"""
    plan = plan_data['plan']
    dinero = plan_data['dinero']

    response = f"📈 **Datos Detallados del Plan '{plan.nombre}'**\n\n"

    # Income breakdown
    ingresos = dinero.ingresos.all()
    if ingresos:
        response += f"💵 **Ingresos por tipo:**\n"
        for ingreso in ingresos:
            response += f"• {ingreso.nombre}: ${ingreso.cantidad:,.0f} ({ingreso.tipo_ingreso})\n"
        response += f"• **Total ingresos:** ${plan_data['ingresos']:,.0f}\n\n"

    # Expense breakdown by category
    gastos = dinero.gastos.all()
    if gastos:
        response += f"💸 **Gastos por categoría:**\n"
        categorias = {}
        for gasto in gastos:
            cat = gasto.tipo_gasto
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(gasto)

        for cat, gastos_cat in categorias.items():
            total_cat = sum(g.cantidad for g in gastos_cat)
            response += f"• **{cat}:** ${total_cat:,.0f}\n"
            for gasto in gastos_cat[:2]:  # Show top 2 expenses per category
                response += f"  - {gasto.nombre}: ${gasto.cantidad:,.0f}\n"

        response += f"\n• **Total gastos:** ${plan_data['gastos']:,.0f}\n"

    # Financial ratios
    if plan_data['ingresos'] > 0:
        response += f"\n📊 **Ratios Financieros:**\n"
        response += f"• Gastos/Ingresos: {(plan_data['gastos']/plan_data['ingresos'])*100:.1f}%\n"
        response += f"• Ahorro/Ingresos: {((plan_data['ingresos']-plan_data['gastos'])/plan_data['ingresos'])*100:.1f}%\n"

    return response


def get_budget_analysis(plan_data):
    """Analyze budget and provide recommendations"""
    ingresos = plan_data['ingresos']
    gastos = plan_data['gastos']
    balance = plan_data['balance']

    response = f"📊 **Análisis de Presupuesto - Plan '{plan_data['plan'].nombre}'**\n\n"

    if ingresos == 0:
        return "No tienes ingresos registrados. Comienza agregando tus fuentes de ingresos para poder analizar tu presupuesto."

    ratio_gastos = (gastos / ingresos) * 100
    ratio_ahorro = (balance / ingresos) * 100

    response += f"📈 **Tu distribución actual:**\n"
    response += f"• Gastos: {ratio_gastos:.1f}% de ingresos (${gastos:,.0f})\n"
    response += f"• Ahorros: {ratio_ahorro:.1f}% de ingresos (${balance:,.0f})\n\n"

    response += f"🎯 **Distribución recomendada (Regla 50/30/20):**\n"
    response += f"• Necesidades: 50% (${ingresos * 0.5:,.0f})\n"
    response += f"• Deseos: 30% (${ingresos * 0.3:,.0f})\n"
    response += f"• Ahorros/Inversiones: 20% (${ingresos * 0.2:,.0f})\n\n"

    # Analysis and recommendations
    if ratio_gastos > 80:
        response += f"⚠️ **Situación crítica:** Estás gastando más del 80% de tus ingresos.\n"
        response += f"💡 **Recomendaciones:**\n"
        response += f"• Reduce gastos en categorías no esenciales\n"
        response += f"• Busca fuentes adicionales de ingresos\n"
        response += f"• Crea un presupuesto mensual detallado\n"
    elif ratio_gastos > 60:
        response += f"⚡ **Situación moderada:** Tus gastos están altos.\n"
        response += f"💡 **Recomendaciones:**\n"
        response += f"• Revisa gastos en entretenimiento y comer fuera\n"
        response += f"• Considera aumentar tus ahorros gradualmente\n"
        response += f"• Rastrea tus gastos por 30 días\n"
    else:
        response += f"✅ **Excelente control:** Tus gastos están bien manejados.\n"
        response += f"💡 **Recomendaciones:**\n"
        response += f"• Mantén este nivel de disciplina\n"
        response += f"• Considera aumentar tus inversiones\n"
        response += f"• Revisa si puedes optimizar algunos gastos menores\n"

    return response


def get_expense_breakdown(plan_data):
    """Provide detailed expense analysis"""
    dinero = plan_data['dinero']
    gastos = dinero.gastos.all()

    if not gastos:
        return "No tienes gastos registrados en este plan. Comienza agregando tus gastos para poder analizarlos."

    response = f"💸 **Análisis de Gastos - Plan '{plan_data['plan'].nombre}'**\n\n"

    # Group expenses by category
    categorias = {}
    for gasto in gastos:
        cat = gasto.tipo_gasto
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(gasto)

    # Sort categories by total amount
    categorias_ordenadas = sorted(categorias.items(),
                                key=lambda x: sum(g.cantidad for g in x[1]),
                                reverse=True)

    total_gastos = plan_data['gastos']

    for cat, gastos_cat in categorias_ordenadas:
        total_cat = sum(g.cantidad for g in gastos_cat)
        porcentaje = (total_cat / total_gastos) * 100 if total_gastos > 0 else 0

        response += f"📁 **{cat}** - ${total_cat:,.0f} ({porcentaje:.1f}%)\n"

        # Show individual expenses in this category (top 3)
        gastos_ordenados = sorted(gastos_cat, key=lambda x: x.cantidad, reverse=True)
        for gasto in gastos_ordenados[:3]:
            response += f"  • {gasto.nombre}: ${gasto.cantidad:,.0f}\n"
        response += "\n"

    # Recommendations based on highest expense categories
    if categorias_ordenadas:
        cat_mayor = categorias_ordenadas[0][0]
        response += f"💡 **Recomendación:** Tu categoría de mayor gasto es '{cat_mayor}'.\n"
        response += f"Considera revisar si puedes optimizar gastos en esta área.\n"

    return response


def get_savings_analysis(plan_data):
    """Analyze savings and provide recommendations"""
    ingresos = plan_data['ingresos']
    gastos = plan_data['gastos']
    balance = plan_data['balance']

    response = f"💰 **Análisis de Ahorros - Plan '{plan_data['plan'].nombre}'**\n\n"

    if ingresos == 0:
        return "No tienes ingresos registrados. Agrega tus ingresos para poder analizar tus ahorros."

    ahorro_mensual = balance
    ratio_ahorro = (ahorro_mensual / ingresos) * 100

    response += f"📊 **Tu situación actual:**\n"
    response += f"• Ahorro mensual: ${ahorro_mensual:,.0f}\n"
    response += f"• Ratio de ahorro: {ratio_ahorro:.1f}%\n"
    response += f"• Meta recomendada: 20% de ingresos\n\n"

    # Emergency fund analysis
    if ahorro_mensual > 0:
        meses_cobertura = ahorro_mensual / gastos * 12 if gastos > 0 else 0
        response += f"🛡️ **Fondo de emergencia:**\n"
        response += f"• Meses de gastos cubiertos: {meses_cobertura:.1f}\n"
        response += f"• Recomendación: 3-6 meses de gastos\n\n"

    # Recommendations
    response += f"💡 **Recomendaciones personalizadas:**\n"

    if ratio_ahorro < 10:
        response += f"• **Prioridad alta:** Aumenta tus ahorros al menos al 20%\n"
        response += f"• Reduce gastos en categorías no esenciales\n"
        response += f"• Busca ingresos adicionales\n"
    elif ratio_ahorro < 20:
        response += f"• **Buen progreso:** Estás cerca de la meta del 20%\n"
        response += f"• Revisa gastos pequeños que se acumulan\n"
        response += f"• Automatiza transferencias a ahorros\n"
    else:
        response += f"• **¡Excelente!** Superas la meta del 20%\n"
        response += f"• Considera invertir parte de tus ahorros\n"
        response += f"• Revisa si puedes aumentar aún más tus ahorros\n"

    # Savings goals
    objetivos_ahorro = [obj for obj in plan_data['objetivos'] if 'ahorro' in obj.nombre.lower() or 'ahorro' in obj.detalles.lower()]
    if objetivos_ahorro:
        response += f"\n🎯 **Metas de ahorro activas:**\n"
        for obj in objetivos_ahorro[:2]:
            progreso = (obj.monto_actual / obj.monto_necesario) * 100 if obj.monto_necesario > 0 else 0
            response += f"• {obj.nombre}: ${obj.monto_actual:,.0f} / ${obj.monto_necesario:,.0f} ({progreso:.1f}%)\n"

    return response


def get_goals_progress(plan_data):
    """Show progress on financial goals"""
    objetivos = plan_data['objetivos']

    if not objetivos:
        return f"No tienes metas establecidas en el plan '{plan_data['plan'].nombre}'. ¿Te gustaría crear algunas metas financieras?"

    response = f"🎯 **Progreso de Metas - Plan '{plan_data['plan'].nombre}'**\n\n"

    # Separate completed and active goals
    completadas = [obj for obj in objetivos if obj.estado == 'completado']
    activas = [obj for obj in objetivos if obj.estado == 'pendiente']

    if completadas:
        response += f"✅ **Metas Completadas ({len(completadas)}):**\n"
        for obj in completadas:
            response += f"• {obj.nombre}: ${obj.monto_necesario:,.0f} ✅\n"
        response += "\n"

    if activas:
        response += f"🔄 **Metas Activas ({len(activas)}):**\n"
        for obj in activas:
            progreso = (obj.monto_actual / obj.monto_necesario) * 100 if obj.monto_necesario > 0 else 0
            restante = obj.monto_necesario - obj.monto_actual
            response += f"• {obj.nombre}\n"
            response += f"  Progreso: ${obj.monto_actual:,.0f} / ${obj.monto_necesario:,.0f} ({progreso:.1f}%)\n"
            response += f"  Restante: ${restante:,.0f}\n\n"

    # Overall progress
    total_objetivos = len(objetivos)
    completadas_count = len(completadas)
    if total_objetivos > 0:
        progreso_general = (completadas_count / total_objetivos) * 100
        response += f"📊 **Progreso General:** {completadas_count}/{total_objetivos} metas completadas ({progreso_general:.1f}%)\n\n"

    # Recommendations
    if activas:
        response += f"💡 **Consejos para alcanzar tus metas:**\n"
        response += f"• Revisa tu presupuesto mensual para destinar más a ahorros\n"
        response += f"• Considera automatizar transferencias a tus metas\n"
        response += f"• Busca ingresos adicionales para acelerar el progreso\n"
        response += f"• Divide metas grandes en objetivos más pequeños y alcanzables\n"
        response += f"• Rastrea tu progreso semanalmente para mantener la motivación\n"

    return response


def get_financial_education(plan_data):
    """Provide comprehensive financial education based on plan data"""
    response = f"🎓 **Educación Financiera Personalizada - Plan '{plan_data['plan'].nombre}'**\n\n"

    # Basic concepts
    response += f"📚 **Conceptos Básicos de Economía que Aplican a Tu Situación:**\n\n"

    # Budget education
    response += f"💰 **Presupuesto Personal:**\n"
    response += f"• **Regla 50/30/20:** 50% necesidades, 30% deseos, 20% ahorros/inversiones\n"
    response += f"• **Tu ratio actual:** {((plan_data['gastos'] / plan_data['ingresos']) * 100) if plan_data['ingresos'] > 0 else 0:.1f}% en gastos\n"
    response += f"• **Inflación:** El costo de vida aumenta ~3% anual. Ajusta tus metas en consecuencia\n"
    response += f"• **Interés compuesto:** Pequeñas cantidades regulares crecen significativamente con el tiempo\n\n"

    # Savings education
    response += f"🏦 **Estrategias de Ahorro:**\n"
    response += f"• **Fondo de Emergencia:** 3-6 meses de gastos. Tú tienes: {plan_data['balance'] / plan_data['gastos'] * 12 if plan_data['gastos'] > 0 else 0:.1f} meses\n"
    response += f"• **Ahorro Automático:** Configura transferencias automáticas el día de pago\n"
    response += f"• **Redondeo:** Redondea compras al dólar más cercano y ahorra la diferencia\n"
    response += f"• **Regla del 1%:** Aumenta gradualmente tus ahorros en incrementos del 1%\n\n"

    # Investment education
    response += f"📈 **Educación en Inversiones:**\n"
    response += f"• **Riesgo vs Retorno:** Inversiones de mayor riesgo ofrecen mayor retorno potencial\n"
    response += f"• **Diversificación:** No pongas todos los huevos en una canasta\n"
    response += f"• **Horizonte Temporal:** El tiempo es tu mejor aliado en inversiones\n"
    response += f"• **Costos:** Minimiza comisiones y tarifas de transacción\n\n"

    # Debt management
    if plan_data['balance'] < 0:
        response += f"⚠️ **Manejo de Deudas (Aplicando a tu situación actual):**\n"
        response += f"• **Método Bola de Nieve:** Paga primero las deudas más pequeñas para ganar momentum\n"
        response += f"• **Consolidación:** Combina deudas en una con tasa más baja\n"
        response += f"• **Negociación:** Contacta a acreedores para mejores términos\n"
        response += f"• **Prevención:** Evita deudas de consumo no esencial\n\n"

    # Income optimization
    response += f"💼 **Optimización de Ingresos:**\n"
    response += f"• **Ingresos Activos:** Trabajo principal, freelance, negocios\n"
    response += f"• **Ingresos Pasivos:** Inversiones, alquileres, regalías\n"
    response += f"• **Desarrollo Profesional:** Educación continua aumenta el potencial salarial\n"
    response += f"• **Múltiples Fuentes:** Reduce riesgo al tener varios streams de ingresos\n\n"

    # Behavioral finance
    response += f"🧠 **Finanzas Conductuales:**\n"
    response += f"• **Sesgo de Confirmación:** Busca opiniones contrarias a tus creencias\n"
    response += f"• **Miedo y Codicia:** Las emociones afectan las decisiones financieras\n"
    response += f"• **Efecto Ancla:** No te dejes influenciar por precios iniciales\n"
    response += f"• **Planificación:** Establece reglas y síguelas disciplinadamente\n\n"

    # Advanced concepts
    response += f"🚀 **Conceptos Avanzados:**\n"
    response += f"• **Asset Allocation:** Distribuye inversiones entre acciones, bonos, bienes raíces\n"
    response += f"• **Rebalancing:** Ajusta periódicamente tu portafolio\n"
    response += f"• **Tax Efficiency:** Minimiza impuestos legalmente\n"
    response += f"• **Legacy Planning:** Planifica para futuras generaciones\n\n"

    # Personalized recommendations
    response += f"🎯 **Recomendaciones Específicas para Ti:**\n"

    if plan_data['balance'] > 1000:
        response += f"• **Alta Prioridad:** Establece un fondo de emergencia antes de invertir\n"
        response += f"• **Acción:** Automatiza el 10% de tus ingresos a ahorros\n"
    elif plan_data['balance'] > 0:
        response += f"• **Próximo paso:** Aumenta tus inversiones conservadoras\n"
        response += f"• **Meta:** Alcanza el 20% de ahorro mensual\n"
    else:
        response += f"• **Situación crítica:** Enfócate en equilibrar ingresos y gastos primero\n"

    if plan_data['objetivos']:
        response += f"• **Metas Específicas:** Revisa tus objetivos y ajusta según tu situación actual\n"

    response += f"\n📚 **Recursos de Aprendizaje Recomendados:**\n"
    response += f"• Libros: 'El Inversor Inteligente', 'Padre Rico Padre Pobre', 'Los secretos de la mente millonaria'\n"
    response += f"• Cursos: Finanzas personales en Coursera, edX, Udemy\n"
    response += f"• Podcasts: 'Planet Money', 'The Dave Ramsey Show'\n"
    response += f"• Apps: Mint, YNAB, Personal Capital para seguimiento\n"

    return response


def get_market_insights(plan_data):
    """Provide market insights and economic trends"""
    response = f"📊 **Análisis de Mercado y Tendencias Económicas**\n\n"

    response += f"🌍 **Tendencias Económicas Globales:**\n"
    response += f"• **Inflación:** Afecta el poder adquisitivo. Ajusta presupuestos anualmente\n"
    response += f"• **Tipos de Interés:** Bajos favorecen inversiones, altos favorecen ahorros\n"
    response += f"• **Crecimiento Económico:** Ciclos afectan empleos e inversiones\n"
    response += f"• **Geopolítica:** Eventos globales impactan mercados financieros\n\n"

    response += f"💹 **Mercados Financieros:**\n"
    response += f"• **Acciones:** Retorno histórico promedio 7-10% anual (con volatilidad)\n"
    response += f"• **Bonos:** Menos volátiles, retorno más bajo y predecible\n"
    response += f"• **Bienes Raíces:** Protección contra inflación, pero menos líquido\n"
    response += f"• **Criptomonedas:** Alto riesgo, alta volatilidad, potencial especulativo\n\n"

    response += f"📈 **Estrategias de Inversión por Perfil:**\n"

    # Conservative profile
    if plan_data['balance'] < plan_data['ingresos'] * 0.1:
        response += f"🛡️ **Perfil Conservador (Recomendado para ti):**\n"
        response += f"• 70% Bonos/Cuentas de ahorro de alto rendimiento\n"
        response += f"• 20% ETFs indexados (baja volatilidad)\n"
        response += f"• 10% Bienes raíces (REITs)\n"
        response += f"• **Horizonte:** Corto plazo, foco en preservación de capital\n\n"

    # Moderate profile
    elif plan_data['balance'] < plan_data['ingresos'] * 0.3:
        response += f"⚖️ **Perfil Moderado (Recomendado para ti):**\n"
        response += f"• 50% ETFs indexados y fondos mutuos\n"
        response += f"• 30% Bonos y cuentas de ahorro\n"
        response += f"• 20% Bienes raíces y alternativas\n"
        response += f"• **Horizonte:** Mediano plazo, balance riesgo-retorno\n\n"

    # Aggressive profile
    else:
        response += f"🚀 **Perfil Agresivo (Recomendado para ti):**\n"
        response += f"• 60% Acciones individuales y ETFs\n"
        response += f"• 20% Bienes raíces y private equity\n"
        response += f"• 20% Bonos para estabilidad mínima\n"
        response += f"• **Horizonte:** Largo plazo, mayor tolerancia al riesgo\n\n"

    response += f"🎯 **Consejos Prácticos de Inversión:**\n"
    response += f"• **Dollar-Cost Averaging:** Invierte cantidades fijas regularmente\n"
    response += f"• **Rebalancing Anual:** Ajusta portafolio una vez al año\n"
    response += f"• **Tax-Loss Harvesting:** Compensar ganancias con pérdidas\n"
    response += f"• **Long-term Mindset:** Los mercados suben con el tiempo\n\n"

    response += f"⚠️ **Riesgos a Considerar:**\n"
    response += f"• **Volatilidad:** Mercados bajan, pero históricamente recuperan\n"
    response += f"• **Inflación:** Erosiona retornos reales de inversiones\n"
    response += f"• **Liquidez:** Algunos activos son difíciles de vender rápidamente\n"
    response += f"• **Comisiones:** Minimiza costos de transacción\n\n"

    response += f"📚 **Recursos de Aprendizaje:**\n"
    response += f"• Libros: 'El Inversor Inteligente', 'Padre Rico Padre Pobre'\n"
    response += f"• Cursos: Finanzas personales en plataformas online\n"
    response += f"• Apps: Rastreadores de gastos e inversiones\n"
    response += f"• Asesores: Consulta profesionales para situaciones complejas\n"

    return response


def get_risk_assessment(plan_data):
    """Assess financial risk tolerance and provide recommendations"""
    response = f"⚖️ **Evaluación de Tolerancia al Riesgo - Plan '{plan_data['plan'].nombre}'**\n\n"

    # Risk assessment based on current situation
    ingresos = float(plan_data['ingresos'])
    gastos = float(plan_data['gastos'])
    balance = float(plan_data['balance'])

    # Calculate risk score (0-100, higher = more risk tolerance)
    risk_score = 50  # Base score

    # Age factor (assuming based on plan maturity - this is approximate)
    # Newer plans might indicate younger users
    plan_age_days = (timezone.now().date() - plan_data['plan'].fecha_creacion.date()).days
    if plan_age_days < 30:
        risk_score += 10  # Newer users might be more risk-tolerant
    elif plan_age_days > 365:
        risk_score -= 10  # Established plans might be more conservative

    # Financial stability factor
    if balance > ingresos * 0.5:
        risk_score += 15  # Strong financial position
    elif balance > ingresos * 0.2:
        risk_score += 5   # Moderate position
    elif balance < 0:
        risk_score -= 20  # Negative position reduces risk tolerance

    # Savings rate factor
    if ingresos > 0:
        savings_rate = balance / ingresos
        if savings_rate > 0.3:
            risk_score += 10
        elif savings_rate > 0.1:
            risk_score += 5
        elif savings_rate < 0:
            risk_score -= 15

    # Goals factor
    if plan_data['objetivos']:
        long_term_goals = [obj for obj in plan_data['objetivos'] if 'jubilacion' in obj.nombre.lower() or 'pension' in obj.nombre.lower()]
        if long_term_goals:
            risk_score += 10  # Long-term goals suggest higher risk tolerance

    # Clamp score between 0-100
    risk_score = max(0, min(100, risk_score))

    response += f"📊 **Tu Puntaje de Tolerancia al Riesgo:** {risk_score}/100\n\n"

    # Risk profile interpretation
    if risk_score >= 70:
        response += f"🔥 **Perfil: Muy Agresivo**\n"
        response += f"• Alto apetito por riesgo\n"
        response += f"• Cómodo con volatilidad significativa\n"
        response += f"• Horizonte de inversión largo (>10 años)\n"
        response += f"• Busca retornos altos, acepta pérdidas temporales\n\n"

        response += f"💡 **Recomendaciones:**\n"
        response += f"• 70% Acciones individuales y ETFs agresivos\n"
        response += f"• 20% Bienes raíces y private equity\n"
        response += f"• 10% Bonos para estabilidad mínima\n"
        response += f"• Considera criptomonedas y startups\n\n"

    elif risk_score >= 50:
        response += f"⚖️ **Perfil: Moderado**\n"
        response += f"• Balance entre riesgo y seguridad\n"
        response += f"• Acepta volatilidad moderada\n"
        response += f"• Horizonte de inversión mediano (5-10 años)\n"
        response += f"• Busca crecimiento con protección de capital\n\n"

        response += f"💡 **Recomendaciones:**\n"
        response += f"• 50% ETFs indexados y fondos mutuos\n"
        response += f"• 30% Bonos y cuentas de ahorro\n"
        response += f"• 20% Bienes raíces y alternativas\n"
        response += f"• Rebalancea portafolio anualmente\n\n"

    elif risk_score >= 30:
        response += f"🛡️ **Perfil: Conservador**\n"
        response += f"• Prefiere seguridad sobre retornos altos\n"
        response += f"• Evita volatilidad significativa\n"
        response += f"• Horizonte de inversión corto (1-5 años)\n"
        response += f"• Prioriza preservación de capital\n\n"

        response += f"💡 **Recomendaciones:**\n"
        response += f"• 60% Bonos y cuentas de ahorro alto rendimiento\n"
        response += f"• 30% ETFs conservadores y fondos balanceados\n"
        response += f"• 10% Bienes raíces (REITs)\n"
        response += f"• Evita inversiones especulativas\n\n"

    else:
        response += f"🐌 **Perfil: Muy Conservador**\n"
        response += f"• Máxima prioridad en seguridad\n"
        response += f"• Intolerante a cualquier pérdida\n"
        response += f"• Horizonte de inversión muy corto (<1 año)\n"
        response += f"• Enfocado en preservación total de capital\n\n"

        response += f"💡 **Recomendaciones:**\n"
        response += f"• 80% Cuentas de ahorro y CDs\n"
        response += f"• 15% Bonos gubernamentales\n"
        response += f"• 5% ETFs ultra-conservadores\n"
        response += f"• Evita todas las inversiones de riesgo\n\n"

    response += f"🔄 **Factores que Influyeron en tu Evaluación:**\n"
    response += f"• **Estabilidad Financiera:** {'Alta' if balance > ingresos * 0.2 else 'Moderada' if balance > 0 else 'Baja'}\n"
    response += f"• **Tasa de Ahorro:** {balance / ingresos * 100 if ingresos > 0 else 0:.1f}%\n"
    response += f"• **Metas a Largo Plazo:** {'Sí' if any('jubilacion' in obj.nombre.lower() or 'pension' in obj.nombre.lower() for obj in plan_data['objetivos']) else 'No'}\n"
    response += f"• **Antigüedad del Plan:** {plan_age_days} días\n\n"

    response += f"⚠️ **Importante:** Esta es una evaluación básica. Considera consultar con un asesor financiero profesional para una evaluación más precisa de tu tolerancia al riesgo.\n\n"

    response += f"📈 **Cómo Ajustar tu Tolerancia al Riesgo:**\n"
    response += f"• **Aumentar:** Construye reservas de emergencia, educa sobre inversiones\n"
    response += f"• **Reducir:** Si experimentas stress por volatilidad, opta por opciones más seguras\n"
    response += f"• **Reevaluar:** Anualmente o después de cambios significativos en tu vida\n"

    return response


def get_tax_optimization(plan_data):
    """Provide tax optimization strategies"""
    response = f"💼 **Optimización Fiscal - Plan '{plan_data['plan'].nombre}'**\n\n"

    response += f"📋 **Estrategias de Optimización Fiscal Generales:**\n\n"

    response += f"🏦 **Ahorros e Inversiones:**\n"
    response += f"• **Cuentas IRA/Roth IRA:** Crecimiento libre de impuestos\n"
    response += f"• **Cuentas 401(k):** Deducibles de impuestos sobre la renta\n"
    response += f"• **Cuentas de Salud (HSA):** Triple beneficio fiscal\n"
    response += f"• **Municipal Bonds:** Intereses libres de impuestos federales\n\n"

    response += f"🏠 **Bienes Raíces:**\n"
    response += f"• **Hipoteca:** Intereses deducibles (hasta ciertos límites)\n"
    response += f"• **Depreciación:** Deducciones por desgaste de propiedades\n"
    response += f"• **1031 Exchange:** Diferir impuestos en reinversión\n"
    response += f"• **REITs:** Dividendos passthrough (evitan doble tributación)\n\n"

    response += f"💼 **Ingresos y Negocios:**\n"
    response += f"• **Deducción de Gastos:** Gastos de negocio legítimos\n"
    response += f"• **Home Office:** Deducción si trabajas desde casa\n"
    response += f"• **Vehículo:** Deducción por uso comercial\n"
    response += f"• **Educación:** Créditos fiscales por educación superior\n\n"

    response += f"📈 **Inversiones:**\n"
    response += f"• **Capital Gains:** Tasas preferenciales para inversiones a largo plazo\n"
    response += f"• **Tax-Loss Harvesting:** Compensar ganancias con pérdidas\n"
    response += f"• **Dividendos Calificados:** Tasas reducidas vs dividendos ordinarios\n"
    response += f"• **Opciones:** Estrategias para diferir o reducir impuestos\n\n"

    response += f"🎯 **Estrategias Avanzadas:**\n"
    response += f"• **Asset Location:** Coloca activos de alta tributación en cuentas tax-advantaged\n"
    response += f"• **Roth Conversion:** Convierte IRAs tradicionales a Roth estratégicamente\n"
    response += f"• **Charitable Remainder Trust:** Beneficios fiscales y flujo de ingresos\n"
    response += f"• **Life Insurance Trusts:** Evitan impuestos estate\n\n"

    # Personalized recommendations based on plan data
    response += f"🎯 **Recomendaciones Personalizadas para Ti:**\n"

    if plan_data['balance'] > 1000:
        response += f"• **Alta Prioridad:** Maximiza contribuciones a cuentas de jubilación\n"
        response += f"• **Considera:** Roth IRA si esperas bracket fiscal más alto en el futuro\n"
        response += f"• **Explora:** Municipal bonds para ingresos libres de impuestos\n"

    if plan_data['ingresos'] > 50000:
        response += f"• **Bracket Fiscal Alto:** Enfócate en deducciones y créditos fiscales\n"
        response += f"• **Considera:** Charitable donations para reducir impuesto sobre la renta\n"
        response += f"• **Evalúa:** Business deductions si tienes ingresos freelance\n"

    if plan_data['gastos'] > plan_data['ingresos'] * 0.7:
        response += f"• **Gastos Altos:** Busca deducciones para reducir carga fiscal efectiva\n"
        response += f"• **Considera:** Itemized deductions vs standard deduction\n"

    response += f"\n⚠️ **Importante:**\n"
    response += f"• Consulta con un contador o asesor fiscal certificado\n"
    response += f"• Las leyes fiscales cambian frecuentemente\n"
    response += f"• Mantén registros detallados de todas las transacciones\n"
    response += f"• No evadas impuestos - optimiza legalmente\n\n"

    response += f"📚 **Recursos Adicionales:**\n"
    response += f"• IRS Publication 550 (Investment Income)\n"
    response += f"• IRS Publication 334 (Tax Guide for Small Business)\n"
    response += f"• Software de preparación de impuestos\n"
    response += f"• Asesores fiscales certificados (CPA)\n"

    return response


def get_estate_planning(plan_data):
    """Provide estate planning and wealth transfer advice"""
    response = f"🏛️ **Planificación Patrimonial - Plan '{plan_data['plan'].nombre}'**\n\n"

    response += f"📋 **Conceptos Básicos de Planificación Patrimonial:**\n\n"

    response += f"📜 **Testamento y Fideicomisos:**\n"
    response += f"• **Testamento:** Distribuye activos según tus deseos\n"
    response += f"• **Fideicomisos Revocables:** Evitan probate, mantienen control\n"
    response += f"• **Fideicomisos Irrevocables:** Protección de activos, beneficios fiscales\n"
    response += f"• **Poderes Notariales:** Designa quién toma decisiones si no puedes\n\n"

    response += f"🏦 **Beneficiarios y Transferencias:**\n"
    response += f"• **Beneficiarios Primarios/Contingentes:** Múltiples niveles de respaldo\n"
    response += f"• **Transferencias Anuales:** Regalo hasta $18,000/persona libre de impuestos\n"
    response += f"• **529 Plans:** Educación con beneficios fiscales\n"
    response += f"• **Life Insurance Trusts:** Evitan impuestos estate\n\n"

    response += f"💰 **Estrategias de Minimización de Impuestos:**\n"
    response += f"• **Exención Estate:** $13.61M (2024) libre de impuestos estate\n"
    response += f"• **Portability:** Transferir exención no utilizada al cónyuge\n"
    response += f"• **Annual Exclusion:** Regalos libres de impuestos\n"
    response += f"• **GST Tax Exemption:** $13.61M para generaciones futuras\n\n"

    response += f"🛡️ **Protección de Activos:**\n"
    response += f"• **Asset Protection Trusts:** Protección contra demandas\n"
    response += f"• **Life Insurance:** Proporciona liquidez al estate\n"
    response += f"• **Business Succession:** Planifica continuidad de negocios\n"
    response += f"• **Guardianship:** Designa tutores para menores\n\n"

    # Personalized recommendations
    response += f"🎯 **Recomendaciones Basadas en tu Situación:**\n"

    if plan_data['balance'] > 10000:
        response += f"• **Prioridad:** Establece testamento y poderes notariales\n"
        response += f"• **Considera:** Fideicomisos para proteger activos familiares\n"
        response += f"• **Evalúa:** Beneficios de life insurance para tu estate\n"

    if plan_data['objetivos']:
        response += f"• **Metas Familiares:** Asegura que tus objetivos incluyan protección familiar\n"
        response += f"• **Beneficiarios:** Actualiza designaciones regularmente\n"

    response += f"\n⚠️ **Consideraciones Importantes:**\n"
    response += f"• Las leyes varían por jurisdicción\n"
    response += f"• Revisa planes anualmente o después de cambios mayores\n"
    response += f"• Combina con planificación financiera integral\n"
    response += f"• Consulta con abogados especializados en estate planning\n\n"

    response += f"📚 **Próximos Pasos:**\n"
    response += f"1. Reúne información sobre tus activos\n"
    response += f"2. Identifica beneficiarios deseados\n"
    response += f"3. Consulta con attorney especializado\n"
    response += f"4. Actualiza designaciones regularmente\n"
    response += f"5. Revisa cobertura de seguro de vida\n"

    return response


def get_tasks_summary(plan_data):
    """Show summary of tasks and to-do items"""
    tareas = plan_data['tareas']

    if not tareas:
        return f"No tienes tareas pendientes en el plan '{plan_data['plan'].nombre}'. ¿Te gustaría crear algunas tareas financieras?"

    response = f"📝 **Tareas y Recordatorios - Plan '{plan_data['plan'].nombre}'**\n\n"

    # Separate by status
    pendientes = [t for t in tareas if t.estado == 'pendiente']
    en_proceso = [t for t in tareas if t.estado == 'en_proceso']
    completadas = [t for t in tareas if t.estado == 'completada']

    if pendientes:
        response += f"⏳ **Pendientes ({len(pendientes)}):**\n"
        for tarea in pendientes[:5]:  # Show top 5
            fecha = tarea.fecha_a_completar.strftime('%d/%m/%Y') if tarea.fecha_a_completar else 'Sin fecha'
            response += f"• {tarea.nombre} ({tarea.tipo_tarea}) - Vence: {fecha}\n"
        response += "\n"

    if en_proceso:
        response += f"🔄 **En Proceso ({len(en_proceso)}):**\n"
        for tarea in en_proceso[:3]:
            response += f"• {tarea.nombre} ({tarea.tipo_tarea})\n"
        response += "\n"

    if completadas:
        response += f"✅ **Completadas ({len(completadas)}):**\n"
        completadas_recientes = sorted(completadas, key=lambda x: x.fecha_completado or x.fecha_guardado, reverse=True)[:3]
        for tarea in completadas_recientes:
            response += f"• {tarea.nombre} ✅\n"

    # Summary
    total = len(tareas)
    response += f"\n📊 **Resumen:** {len(pendientes)} pendientes, {len(en_proceso)} en proceso, {len(completadas)} completadas\n"

    return response


def get_investment_recommendations(plan_data):
    """Provide investment recommendations based on plan data"""
    ingresos = plan_data['ingresos']
    gastos = plan_data['gastos']
    balance = plan_data['balance']

    response = f"📈 **Recomendaciones de Inversión - Plan '{plan_data['plan'].nombre}'**\n\n"

    response += f"💰 **Tu capacidad de inversión:**\n"
    response += f"• Balance disponible: ${balance:,.0f}\n"
    response += f"• Ahorro mensual: ${balance:,.0f}\n\n"

    # Risk assessment based on financial situation
    if balance < 0:
        response += f"⚠️ **No recomendado invertir ahora**\n"
        response += f"Primero estabiliza tus finanzas y crea un balance positivo.\n\n"
        response += f"💡 **Pasos previos:**\n"
        response += f"• Reduce gastos innecesarios\n"
        response += f"• Aumenta tus ingresos\n"
        response += f"• Construye un fondo de emergencia (3-6 meses de gastos)\n"

    elif balance < ingresos * 0.1:  # Less than 10% of monthly income
        response += f"🔰 **Principiante - Inversión conservadora**\n\n"
        response += f"💡 **Recomendaciones:**\n"
        response += f"• **Cuentas de ahorro de alto rendimiento** (4-5% APY)\n"
        response += f"• **Certificados de depósito** (CDs) a corto plazo\n"
        response += f"• **Fondos mutuos de dinero** (Money Market Funds)\n\n"
        response += f"🎯 **Monto sugerido:** $100-500 inicial\n"

    elif balance < ingresos * 0.3:  # 10-30% of monthly income
        response += f"📈 **Intermedio - Inversión moderada**\n\n"
        response += f"💡 **Recomendaciones:**\n"
        response += f"• **ETFs de bonos** (diversificación de renta fija)\n"
        response += f"• **Fondos indexados** (S&P 500, Total Stock Market)\n"
        response += f"• **Cuentas de jubilación** (401k, IRA)\n\n"
        response += f"🎯 **Asignación sugerida:** 60% acciones, 40% bonos\n"

    else:  # More than 30% of monthly income available
        response += f"🚀 **Avanzado - Inversión agresiva**\n\n"
        response += f"💡 **Recomendaciones:**\n"
        response += f"• **ETFs sectoriales** (tecnología, salud, energía)\n"
        response += f"• **Criptomonedas** (pequeño porcentaje, alto riesgo)\n"
        response += f"• **Bienes raíces** (REITs o crowdfunding)\n"
        response += f"• **Inversiones alternativas** (private equity, venture capital)\n\n"
        response += f"🎯 **Asignación sugerida:** 70-80% acciones, 20-30% alternativas\n"

    # General advice
    response += f"📚 **Consejos generales de inversión:**\n"
    response += f"• Diversifica tu portafolio\n"
    response += f"• Invierte regularmente (dollar-cost averaging)\n"
    response += f"• Considera tus objetivos y horizonte temporal\n"
    response += f"• Educa continuamente sobre mercados financieros\n"
    response += f"• Consulta con un asesor financiero si es necesario\n"

    return response


def get_personalized_advice(plan_data):
    """Generate personalized financial advice based on plan data"""
    ingresos = plan_data['ingresos']
    gastos = plan_data['gastos']
    balance = plan_data['balance']
    objetivos = plan_data['objetivos']
    tareas = plan_data['tareas']

    response = f"🎯 **Consejos Personalizados - Plan '{plan_data['plan'].nombre}'**\n\n"

    # Analyze financial health
    if ingresos == 0:
        response += f"📝 **Situación inicial:** No tienes ingresos registrados.\n\n"
        response += f"💡 **Primeros pasos:**\n"
        response += f"• Registra todos tus ingresos mensuales\n"
        response += f"• Identifica fuentes de ingresos adicionales\n"
        response += f"• Crea un presupuesto básico\n\n"

    elif balance < 0:
        response += f"⚠️ **Situación crítica:** Tu balance es negativo (${balance:,.0f}).\n\n"
        response += f"🚨 **Acciones urgentes:**\n"
        response += f"• Revisa y reduce gastos innecesarios inmediatamente\n"
        response += f"• Contacta a acreedores si tienes deudas\n"
        response += f"• Busca ingresos adicionales (freelance, ventas, etc.)\n"
        response += f"• Crea un presupuesto de supervivencia\n\n"

    elif balance < ingresos * 0.1:
        response += f"⚡ **Situación básica:** Tienes un balance positivo pequeño.\n\n"
        response += f"💡 **Próximos pasos:**\n"
        response += f"• Construye un fondo de emergencia (3 meses de gastos)\n"
        response += f"• Reduce gastos en categorías no esenciales\n"
        response += f"• Automatiza transferencias de ahorro\n"
        response += f"• Establece metas financieras realistas\n\n"

    elif balance < ingresos * 0.2:
        response += f"📈 **Buen progreso:** Estás ahorrando moderadamente.\n\n"
        response += f"💡 **Optimizaciones:**\n"
        response += f"• Revisa gastos por categoría para identificar ahorros\n"
        response += f"• Considera inversiones conservadoras\n"
        response += f"• Aumenta gradualmente tus metas de ahorro\n"
        response += f"• Educa sobre inversiones básicas\n\n"

    else:
        response += f"✅ **Excelente situación:** Superas el 20% de ahorro recomendado.\n\n"
        response += f"💡 **Estrategias avanzadas:**\n"
        response += f"• Diversifica tus inversiones\n"
        response += f"• Considera aumentar ingresos pasivos\n"
        response += f"• Revisa oportunidades de inversión\n"
        response += f"• Planifica para metas a largo plazo\n\n"

    # Goals analysis
    if objetivos:
        objetivos_pendientes = [obj for obj in objetivos if obj.estado == 'pendiente']
        if objetivos_pendientes:
            response += f"🎯 **Sobre tus metas:**\n"
            obj_mas_cercano = min(objetivos_pendientes, key=lambda x: (x.monto_actual / x.monto_necesario) if x.monto_necesario > 0 else 0, default=None)
            if obj_mas_cercano:
                progreso = (obj_mas_cercano.monto_actual / obj_mas_cercano.monto_necesario) * 100 if obj_mas_cercano.monto_necesario > 0 else 0
                response += f"• Tu meta más cercana a completarse es '{obj_mas_cercano.nombre}' ({progreso:.1f}%)\n"
                response += f"• Restante: ${obj_mas_cercano.monto_necesario - obj_mas_cercano.monto_actual:,.0f}\n\n"

    # Tasks analysis
    if tareas:
        tareas_pendientes = [t for t in tareas if t.estado != 'completada']
        if tareas_pendientes:
            response += f"📝 **Tareas pendientes:**\n"
            tareas_urgentes = [t for t in tareas_pendientes if t.fecha_a_completar and t.fecha_a_completar <= timezone.now().date() + timezone.timedelta(days=7)]
            if tareas_urgentes:
                response += f"• Tienes {len(tareas_urgentes)} tareas urgentes (próximos 7 días)\n"
            response += f"• Total pendientes: {len(tareas_pendientes)}\n\n"

    # Final recommendations
    response += f"🚀 **Recomendaciones finales:**\n"
    response += f"• Revisa tu presupuesto semanalmente\n"
    response += f"• Rastrea todos tus gastos por al menos 30 días\n"
    response += f"• Establece recordatorios para pagos importantes\n"
    response += f"• Educa continuamente sobre finanzas personales\n"
    response += f"• Celebra pequeños logros financieros\n"

    return response
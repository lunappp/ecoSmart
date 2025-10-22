from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
from Planes_app.models import Plan, Dinero, Ingreso, Gasto, Objetivo, Tarea
from mistralai import Mistral
import os
from django.conf import settings

@login_required
def chatbot_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, creador=request.user)
    messages = Message.objects.filter(user=request.user, plan=plan).order_by('timestamp')
    return render(request, 'chatbot/chatbot.html', {'messages': messages, 'plan': plan})

@login_required
def send_message(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, creador=request.user)
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Get AI response with plan context
            bot_response = get_ai_response(user_message, plan, request.user)
            # Save to database
            Message.objects.create(
                user=request.user,
                plan=plan,
                user_message=user_message,
                bot_response=bot_response
            )
            return JsonResponse({'response': bot_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_ai_response(message, plan, user):
    try:
        # Initialize Mistral client
        client = Mistral(api_key=settings.MISTRAL_API_KEY)

        # Get plan data for context
        plan_data = get_plan_context(plan)

        # Create system prompt with economics knowledge and plan data
        system_prompt = f"""Eres un asistente económico inteligente especializado en finanzas personales y economía.
        Tienes acceso a los datos financieros del usuario para dar consejos personalizados.

        CONOCIMIENTOS ECONÓMICOS:
        {settings.ECONOMICS_KNOWLEDGE}

        DATOS DEL PLAN FINANCIERO DEL USUARIO:
        {plan_data}

        INSTRUCCIONES:
        - Responde preguntas básicas sobre economía usando el conocimiento proporcionado
        - Da consejos personalizados basados en los datos financieros del usuario
        - Mantén conversaciones naturales y útiles
        - Si no tienes suficiente información, pide más detalles
        - Sé amable y profesional
        - Responde en español ya que el usuario está en Argentina
        - Mantén las respuestas concisas y directas, sin texto innecesario
        - Limita las respuestas a 2-3 párrafos máximo
        - Evita explicaciones largas, ve al grano
        - SIEMPRE usa listas con viñetas (-) o numeradas (1., 2., etc.) para enumerar consejos, pasos o elementos
        - SIEMPRE divide las respuestas en párrafos cortos separados por líneas en blanco
        - Formatea el texto de manera clara y visualmente atractiva, usando saltos de línea para separar ideas
        - Para consejos financieros, estructura siempre en lista numerada
        - Para explicaciones, usa párrafos separados

        Si el usuario pregunta sobre sus finanzas específicas, usa los datos del plan para dar consejos relevantes."""

        # Create chat completion
        response = client.chat.complete(
            model="mistral-tiny",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content

    except Exception as e:
        # Log the error for debugging
        print(f"AI Response Error: {str(e)}")
        return f"Lo siento, tuve un problema técnico: {str(e)}. Por favor, contacta al administrador."

def get_plan_context(plan):
    """Get financial data from the plan for AI context"""
    try:
        dinero = plan.dinero
        ingresos = dinero.ingresos.all()
        gastos = dinero.gastos.all()
        objetivos = plan.objetivos.all()
        tareas = plan.tareas.all()

        context = f"""
        PLAN: {plan.nombre}
        DESCRIPCIÓN: {plan.descripcion}
        TIPO: {plan.get_tipo_plan_display()}

        DINERO TOTAL: ${dinero.total_dinero}
        GASTO TOTAL: ${dinero.gasto_total}
        INGRESO TOTAL: ${dinero.ingreso_total}

        INGRESOS RECIENTES:
        """

        for ingreso in ingresos[:5]:  # Last 5 incomes
            context += f"- {ingreso.nombre}: ${ingreso.cantidad} ({ingreso.get_tipo_ingreso_display()})\n"

        context += "\nGASTOS RECIENTES:\n"
        for gasto in gastos[:5]:  # Last 5 expenses
            context += f"- {gasto.nombre}: ${gasto.cantidad} ({gasto.get_tipo_gasto_display()})\n"

        context += "\nOBJETIVOS:\n"
        for objetivo in objetivos:
            progreso = (objetivo.monto_actual / objetivo.monto_necesario * 100) if objetivo.monto_necesario > 0 else 0
            context += f"- {objetivo.nombre}: ${objetivo.monto_actual}/${objetivo.monto_necesario} ({progreso:.1f}%)\n"

        context += "\nTAREAS PENDIENTES:\n"
        for tarea in tareas.filter(estado='pendiente')[:3]:  # Next 3 pending tasks
            context += f"- {tarea.nombre}: {tarea.descripcion}\n"

        return context

    except Exception as e:
        return f"Error obteniendo datos del plan: {str(e)}"
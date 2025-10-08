from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
import openai
import os

@login_required
def chatbot_view(request):
    messages = Message.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'chatbot/chatbot.html', {'messages': messages})

@login_required
def send_message(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Get AI response
            bot_response = get_ai_response(user_message)
            # Save to database
            Message.objects.create(
                user=request.user,
                user_message=user_message,
                bot_response=bot_response
            )
            return JsonResponse({'response': bot_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_ai_response(message):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return "Hola, soy el asistente de EcoSmart. Para usar la IA completa, configura tu clave de OpenAI. Por ahora, puedo ayudarte con preguntas básicas sobre finanzas."

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente útil para EcoSmart, una aplicación de gestión financiera. Responde en español."},
                {"role": "user", "content": message}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Lo siento, no pude procesar tu mensaje en este momento. Verifica tu conexión a internet o la clave de API."

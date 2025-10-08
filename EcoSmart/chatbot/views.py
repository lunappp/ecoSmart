from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
# import openai  # Temporarily commented out due to installation issues
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
    # Temporarily disabled due to openai installation issues
    return "Hola, soy el asistente de EcoSmart. Actualmente tengo problemas técnicos con la IA. Por favor, contacta al administrador para resolver este inconveniente. Mientras tanto, puedes usar las otras funcionalidades de la aplicación."
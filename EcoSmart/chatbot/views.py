from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
# import openai  # Temporarily commented out due to installation issues
import os
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

# Initialize ChatterBot
chatbot = ChatBot('EcoBot')

# Training data for basic conversation and economics
training_data = [
    # Basic conversation
    "Hola",
    "¡Hola! ¿Cómo estás?",
    "¿Cómo estás?",
    "Estoy bien, gracias. ¿Y tú?",
    "Bien, gracias",
    "Me alegro. ¿En qué puedo ayudarte?",
    "¿Qué tal?",
    "Todo bien, ¿y tú?",
    "Adiós",
    "¡Hasta luego!",
    "Gracias",
    "De nada",

    # Economics basics
    "¿Qué es la inflación?",
    "La inflación es el aumento generalizado y sostenido de los precios de bienes y servicios en un período de tiempo.",
    "¿Qué es el ahorro?",
    "El ahorro es la parte de los ingresos que no se gasta en consumo y se reserva para el futuro.",
    "¿Qué es un presupuesto?",
    "Un presupuesto es un plan financiero que detalla los ingresos y gastos previstos para un período determinado.",
    "¿Qué es la inversión?",
    "La inversión es el acto de destinar dinero o recursos con la expectativa de obtener un beneficio futuro.",
    "¿Qué es el interés compuesto?",
    "El interés compuesto es el interés que se calcula sobre el capital inicial más los intereses acumulados anteriormente.",
    "¿Cómo controlar los gastos?",
    "Para controlar los gastos, es importante hacer un presupuesto, priorizar necesidades sobre deseos y revisar gastos regularmente.",
    "¿Qué es la deuda?",
    "La deuda es una obligación financiera que una persona o entidad tiene con otra.",
    "¿Qué es el crédito?",
    "El crédito es la capacidad de obtener bienes o servicios ahora y pagar por ellos más tarde.",
]

# Train the chatbot
trainer = ListTrainer(chatbot)
trainer.train(training_data)

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
    try:
        response = chatbot.get_response(message)
        return str(response)
    except Exception as e:
        return "Lo siento, no pude procesar tu mensaje. Inténtalo de nuevo."
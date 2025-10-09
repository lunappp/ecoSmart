from django.urls import path
from . import views

urlpatterns = [
    path('plan/<int:plan_id>/', views.chatbot_view, name='chatbot'),
    path('send/<int:plan_id>/', views.send_message, name='send_message'),
]
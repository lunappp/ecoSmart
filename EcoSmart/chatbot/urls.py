from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot'),
    path('plan/<int:plan_id>/', views.chatbot_view, name='chatbot_plan'),
    path('send/', views.send_message, name='send_message'),
    path('send/plan/<int:plan_id>/', views.send_message, name='send_message_plan'),
]
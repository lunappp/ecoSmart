from django.urls import path
from . import views

urlpatterns = [
    path('<int:plan_id>/', views.chatbot_view, name='chatbot'),
    path('<int:plan_id>/send/', views.send_message, name='send_message'),
]
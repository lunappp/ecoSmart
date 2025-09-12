# Planes_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Esta ruta capturará el ID del plan que se elija
    path('<int:plan_id>/', views.Menu_plan, name='Menu_plan'),
]
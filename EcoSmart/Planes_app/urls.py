from django.urls import path
from . import views

urlpatterns = [
    path('<int:plan_id>/', views.menu_plan, name='Menu_plan'),
    
    path('<int:plan_id>/ingresos/', views.ingresos, name='ingresos'),
    path('<int:plan_id>/gastos/', views.gastos, name='gastos'),
    
    path('<int:plan_id>/estadisticas/', views.estadisticas, name='estadisticas'),


    path('<int:plan_id>/objetivos/', views.objetivos, name='objetivos'),
    path('<int:plan_id>/objetivos/agregar/', views.agregar_objetivo, name='agregar_objetivo'),
    path('<int:plan_id>/objetivos/<int:objetivo_id>/aportar/', views.aportar_objetivo, name='aportar_objetivo'),
    
        
    path('<int:plan_id>/tareas/', views.tareas, name='tareas'),
    path('<int:plan_id>/tareas/agregar/', views.agregar_tarea, name='agregar_tarea'),
    path('<int:plan_id>/tareas/<int:tarea_id>/cambiar_estado/', views.cambiar_estado_tarea, name='cambiar_estado_tarea'),
  
]

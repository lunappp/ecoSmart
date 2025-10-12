from django.urls import path
from . import views

urlpatterns = [
    path('<int:plan_id>/', views.menu_plan, name='Menu_plan'),
    path('<int:plan_id>/editar/', views.editar_plan, name='editar_plan'),
    path('<int:plan_id>/ajustes/', views.ajustes, name='ajustes'),

    path('<int:plan_id>/ingresos/', views.ingresos, name='ingresos'),
    path('<int:plan_id>/ingresos/<int:ingreso_id>/editar/', views.editar_ingreso, name='editar_ingreso'),
    path('<int:plan_id>/ingresos/<int:ingreso_id>/eliminar/', views.eliminar_ingreso, name='eliminar_ingreso'),
    
    path('<int:plan_id>/gastos/', views.gastos, name='gastos'),
    path('<int:plan_id>/gastos/<int:gasto_id>/editar/', views.editar_gasto, name='editar_gasto'),
    path('<int:plan_id>/gastos/<int:gasto_id>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),
    
    path('<int:plan_id>/estadisticas/', views.estadisticas, name='estadisticas'),
    path('<int:plan_id>/historiales/', views.historiales, name='historiales'),
    path('<int:plan_id>/historiales/pdf/', views.descargar_pdf_graficos, name='descargar_pdf_graficos'),

    path('<int:plan_id>/objetivos/', views.objetivos, name='objetivos'),
    path('<int:plan_id>/objetivos/agregar/', views.agregar_objetivo, name='agregar_objetivo'),
    path('<int:plan_id>/objetivos/<int:objetivo_id>/aportar/', views.aportar_objetivo, name='aportar_objetivo'),
    path('<int:plan_id>/objetivos/<int:objetivo_id>/editar/', views.editar_objetivo, name='editar_objetivo'),
    path('<int:plan_id>/objetivos/<int:objetivo_id>/eliminar/', views.eliminar_objetivo, name='eliminar_objetivo'),
    
        
    path('<int:plan_id>/tareas/', views.tareas, name='tareas'),
    path('<int:plan_id>/tareas/agregar/', views.agregar_tarea, name='agregar_tarea'),
    path('<int:plan_id>/tareas/<int:tarea_id>/cambiar_estado/', views.cambiar_estado_tarea, name='cambiar_estado_tarea'),
    path('<int:plan_id>/tareas/<int:tarea_id>/editar/', views.editar_tarea, name='editar_tarea'),
    path('<int:plan_id>/tareas/<int:tarea_id>/eliminar/', views.eliminar_tarea, name='eliminar_tarea'),

    path('<int:plan_id>/miembros/buscar/', views.buscar_usuarios, name='buscar_usuarios'),
    path('<int:plan_id>/miembros/cancelar/<int:invitacion_id>/', views.cancelar_invitacion, name='cancelar_invitacion'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('<int:plan_id>/', views.Menu_plan, name='Menu_plan'),
    
        path('<int:plan_id>/ingresos/', views.ingresos, name='ingresos'),
    path('<int:plan_id>/gastos/', views.gastos, name='gastos'),
    
    path('<int:plan_id>/estadisticas/', views.estadisticas, name='estadisticas'),

]

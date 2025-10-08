"""
URL configuration for EcoSmart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
import App.views
import Planes_app.views

urlpatterns = [
    path('admin/', admin.site.urls), 
    #------------------ Landing page ------------------#
    path('',App.views.Landing, name= 'Landing'),
    
    #---------------------- Auth ----------------------#
    path('Register/',App.views.Register, name= 'Register'),
    path('Login/',App.views.Login, name= 'Login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    #------------------- daashboard -------------------#
    path('Dashboard/',App.views.Dashboard, name= 'Dashboard'),
    path('edit_profile/', App.views.edit_profile, name='edit_profile'),
    path('crear_plan/', App.views.crear_plan_view, name='crear_plan'),
    path('aceptar_invitacion/<int:invitacion_id>/', App.views.aceptar_invitacion, name='aceptar_invitacion'),
    path('rechazar_invitacion/<int:invitacion_id>/', App.views.rechazar_invitacion, name='rechazar_invitacion'),
    
    #----------------- menu principal -----------------#
    path('Inicio/',App.views.Inicio, name= 'Inicio'),
    path('transacciones/',App.views.transacciones, name= 'transacciones'),
    #path('Estadisticas/',App.views.Estadisticas, name= 'Estadisticas'),
    
    #----------------------planes-----------------------#
    path('planes/', include('Planes_app.urls')),

    #----------------------chatbot-----------------------#
    path('chatbot/', include('chatbot.urls')),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.shortcuts import render

# Create your views here.


#----------------- menu rpincipal -----------------#
#                        |                         #
#                        v                         #

def Inicio(request):
    return render(request, 'menu_principal/index.html')

def transacciones(request):
    return render(request, 'menu_principal/transacciones.html')

def Estadisticas(request):
    return render(request, 'menu_principal/Estadisticas.html')
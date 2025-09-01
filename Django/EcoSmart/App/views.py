from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User


from App.forms import RegisterForm

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        return render('auth/register.html')
    return render(request, 'home.html')

def login(request):
    if request.method == 'POST':
        print('hola')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username = username, password = password)
        if user is not None:
            return redirect('register')
    else:
        print('hola')
    
    return render(request, 'auth/login.html')

def registerPage(request):
    return render(request, 'auth/register.html')

def register(request):
    if request.method == 'POST':
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            register_form.save()
            return redirect('home')
        else:
            errores = register_form.errors
        
            return render(request, 'auth/register.html', {
                'registerForm': register_form,
                'errores': errores
                
            })
    else:
        
        register_form = RegisterForm()
        return render(request, 'auth/register.html', {
            'registerForm': register_form
        })

    
        

def header(request):
    return render(request, 'header.html')
from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Plan(models.Model):
    """
    Representa un plan individual o grupal.
    """
    TIPO_PLAN_CHOICES = (
        ('individual', 'Individual'),
        ('grupal', 'Grupal'),
    )
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creador = models.ForeignKey(User, related_name='planes_creados', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tipo_plan = models.CharField(max_length=10, choices=TIPO_PLAN_CHOICES, default='individual')
    
    def __str__(self):
        return self.nombre

class Suscripcion(models.Model):
    """
    Conecta a un usuario con un plan.
    """
    usuario = models.ForeignKey(User, related_name='suscripciones', on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, related_name='suscripciones', on_delete=models.CASCADE)
    fecha_suscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'plan') # Asegura que un usuario no pueda suscribirse al mismo plan dos veces

    def __str__(self):
        return f"{self.usuario.username} suscrito a {self.plan.nombre}"
    
class Ingreso(models.Model):
    TIPO_INGRESO_CHOICES = (
        ('salario', 'Salario'),
        ('ganancia', 'Ganancia'),
        ('venta', 'Venta'),
        ('regalo', 'Regalo'),
        ('otro', 'Otro'),
    )
    plan = models.ForeignKey(Plan, related_name='ingresos', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    tipo_ingreso = models.CharField(max_length=50, choices=TIPO_INGRESO_CHOICES, default='salario')
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class Gasto(models.Model):
    TIPO_GASTO_CHOICES = (
        ('alquiler', 'Alquiler'),
        ('comida', 'Comida'),
        ('servicios', 'Servicios'),
        ('entretenimiento', 'Entretenimiento'),
        ('transporte', 'Transporte'),
        ('deuda', 'Deuda'),
        ('otro', 'Otro'),
    )
    plan = models.ForeignKey(Plan, related_name='gastos', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    tipo_gasto = models.CharField(max_length=50, choices=TIPO_GASTO_CHOICES, default='alquiler')
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

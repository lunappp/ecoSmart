from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Plan(models.Model):
    """
    Representa un plan individual o grupal.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creador = models.ForeignKey(User, related_name='planes_creados', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
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
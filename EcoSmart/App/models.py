from django.db import models
from django.contrib.auth.models import User  # <--- ¡Esta es la línea que faltaba!

# El modelo Plan representa tanto planes individuales como grupales
class Plan(models.Model):
    # Relación con el usuario que crea el plan.
    # on_delete=models.CASCADE asegura que si el usuario se elimina, sus planes también.
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Nombre del plan, por ejemplo: "Ahorro para el auto"
    nombre = models.CharField(max_length=100)
    
    # Tipo de plan: 'individual' o 'grupal'
    tipo_plan = models.CharField(max_length=20, default='individual', choices=[
        ('individual', 'Individual'),
        ('grupal', 'Grupal')
    ])
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Plan de {self.usuario.username}: {self.nombre}"

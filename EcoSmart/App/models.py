from django.db import models
from django.contrib.auth.models import User  # <--- ¡Esta es la línea que faltaba!

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

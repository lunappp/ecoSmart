from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


# Obtener el modelo de usuario activo en el proyecto (asumiendo que es App.models.usuario)
User = get_user_model()

class Plan(models.Model):
    TIPO_PLAN_CHOICES = [
        ('individual', 'Individual'),
        ('grupal', 'Grupal'),
    ]

    # id_plan (INTEGER - PK) -> Django lo crea automáticamente
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(max_length=65535)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    tipo_plan = models.CharField(max_length=10, choices=TIPO_PLAN_CHOICES, default='individual')
    imagen = models.ImageField(upload_to='planes/', blank=True, null=True)

    # id_creador (FK a usuario)
    creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='planes_creados')

    def __str__(self):
        return self.nombre

class Suscripcion(models.Model):
    ROL_CHOICES = [
        ('miembro', 'Miembro'),
        ('moderador', 'Moderador'),
        ('admin', 'admin'),
    ]

    # id_suscripcion (INTEGER - PK) -> Django lo crea automáticamente

    # id_usuario (FK a usuario)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suscripciones')

    # id_plan (FK a planes_plan)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='suscripcion')

    fecha_suscripcion = models.DateTimeField(default=timezone.now)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='miembro')

    class Meta:
        # Asegura que un usuario solo pueda suscribirse una vez al mismo plan
        unique_together = ('usuario', 'plan')
        verbose_name_plural = "Suscripciones"

    def __str__(self):
        return f'{self.usuario.username} suscrito a {self.plan.nombre}'

class Dinero(models.Model):
    # id_dinero (INTEGER - PK) -> Django lo crea automáticamente
    
    # id_plan (FK a planes_plan)
    plan = models.OneToOneField(Plan, on_delete=models.CASCADE, related_name='dinero')
    
    total_dinero = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    gasto_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    ingreso_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    class Meta:
        verbose_name_plural = "Dinero (Cuentas)"

    def __str__(self):
        return f'Cuenta de {self.plan.nombre}'

class Ingreso(models.Model):
    TIPO_INGRESO_CHOICES = [
        ('salario', 'Salario'),
        ('inversion', 'Inversión'),
        ('extra', 'Ingreso Extra'),
        ('otro', 'Otro'),
    ]

    # id (INTEGER - PK) -> Django lo crea automáticamente
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(max_length=65535)
    tipo_ingreso = models.CharField(max_length=50, choices=TIPO_INGRESO_CHOICES)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_guardado = models.DateTimeField(default=timezone.now)
    imagen = models.ImageField(upload_to='ingresos/', blank=True, null=True)

    # id_dinero (FK a dinero)
    dinero = models.ForeignKey(Dinero, on_delete=models.CASCADE, related_name='ingresos')

    # Usuario que registró el ingreso
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ingresos', null=True, blank=True)

    def __str__(self):
        return f'Ingreso de {self.cantidad} ({self.nombre})'

class Gasto(models.Model):
    TIPO_GASTO_CHOICES = [
        ('alimentacion', 'Alimentación'),
        ('alquiler', 'Alquiler/Vivienda'),
        ('servicios', 'Servicios'),
        ('transporte', 'Transporte'),
        ('entretenimiento', 'Entretenimiento'),
        ('otro', 'Otro'),
    ]

    # id (INTEGER - PK) -> Django lo crea automáticamente
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(max_length=65535)
    tipo_gasto = models.CharField(max_length=50, choices=TIPO_GASTO_CHOICES)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_guardado = models.DateTimeField(default=timezone.now)
    imagen = models.ImageField(upload_to='gastos/', blank=True, null=True)

    # id_dinero (FK a dinero)
    dinero = models.ForeignKey(Dinero, on_delete=models.CASCADE, related_name='gastos')

    # Usuario que registró el gasto
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gastos', null=True, blank=True)

    def __str__(self):
        return f'Gasto de {self.cantidad} ({self.nombre})'

class Objetivo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
    ]

    # id_objetivo (INTEGER - PK) -> Django lo crea automáticamente

    # id_plan (FK a planes_plan)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='objetivos')

    nombre = models.CharField(max_length=255)
    detalles = models.TextField(max_length=65535)
    monto_necesario = models.DecimalField(max_digits=15, decimal_places=2)
    monto_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='pendiente')
    fecha_guardado = models.DateTimeField(default=timezone.now)
    imagen = models.ImageField(upload_to='objetivos/', blank=True, null=True)

    def __str__(self):
        return self.nombre

class Tarea(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
    ]

    TIPO_TAREA_CHOICES = [
        ('pago', 'Pago'),
        ('recordatorio', 'Recordatorio'),
        ('tramite', 'Trámite'),
        ('otro', 'Otro'),
    ]

    # Relación con el Plan
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='tareas')

    # Usuario asignado para completar la tarea
    usuario_asignado = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tareas_asignadas', null=True, blank=True)

    # Campos del Formulario
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(max_length=65535, null=True, blank=True)
    tipo_tarea = models.CharField(max_length=50, choices=TIPO_TAREA_CHOICES)
    imagen = models.ImageField(upload_to='tareas/', blank=True, null=True)

    # Fechas
    fecha_guardado = models.DateTimeField(default=timezone.now)
    fecha_a_completar = models.DateField(null=True, blank=True) # La fecha límite

    # Campo de Estado (Persistente)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='pendiente')

    # AÑADIDO: Campo para registrar cuándo se completó (necesario para la lógica de "A Tiempo" / "Tarde")
    fecha_completado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Tarea: {self.nombre} ({self.estado})'
    
    # Si quieres usar los campos de estado en el admin o en otro lugar de forma más legible
    def get_estado_display_completo(self):
        # Esta función usa el estado persistente (completada, pendiente, etc.)
        if self.estado == 'completada':
            return "Completada"
        elif self.estado == 'en_proceso':
            return "En Proceso"
        return "Pendiente"

    class Meta:
        verbose_name = "Tarea y Recordatorio"
        verbose_name_plural = "Tareas y Recordatorios"

class Invitacion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='invitaciones')
    invitado = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitaciones_recibidas')
    invitador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitaciones_enviadas')
    fecha_invitacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    class Meta:
        verbose_name = "Invitación"
        verbose_name_plural = "Invitaciones"

    def __str__(self):
        return f'Invitación de {self.invitador.username} a {self.invitado.username} para {self.plan.nombre}'
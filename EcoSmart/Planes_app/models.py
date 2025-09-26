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
    
    # id_creador (FK a usuario)
    creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='planes_creados')

    def __str__(self):
        return self.nombre

class Suscripcion(models.Model):
    # id_suscripcion (INTEGER - PK) -> Django lo crea automáticamente
    
    # id_usuario (FK a usuario)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suscripciones')
    
    # id_plan (FK a planes_plan)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='suscripcion')
    
    fecha_suscripcion = models.DateTimeField(default=timezone.now)

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

    # id_dinero (FK a dinero)
    dinero = models.ForeignKey(Dinero, on_delete=models.CASCADE, related_name='ingresos')

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
    
    # id_dinero (FK a dinero)
    dinero = models.ForeignKey(Dinero, on_delete=models.CASCADE, related_name='gastos')

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

    # id_tareas (INTEGER - PK) -> Django lo crea automáticamente
    
    # id_plan (FK a planes_plan)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='tareas')
    
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(max_length=65535, null=True, blank=True)
    tipo_tarea = models.CharField(max_length=50, choices=TIPO_TAREA_CHOICES)
    fecha_guardado = models.DateTimeField(default=timezone.now)
    fecha_a_completar = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f'Tarea: {self.nombre} ({self.estado})'
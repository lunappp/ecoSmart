from django import forms
from .models import Ingreso, Gasto, Objetivo, Tarea, Plan, Suscripcion

# ------------------------------
# 0. Formularios de CREACIÓN DE PLANES (Usados en App/views.py)
# ------------------------------

class CrearPlanForm(forms.ModelForm):
    """Formulario para crear un nuevo Plan."""
    class Meta:
        model = Plan
        # Excluimos 'creador' y 'fecha_creacion' ya que se asignan en la vista.
        fields = ['nombre', 'descripcion', 'tipo_plan', 'imagen']

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ej: Viaje a Europa 2025'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-textarea w-full rounded-lg border-gray-300 shadow-sm', 'rows': 3, 'placeholder': 'Breve descripción del propósito del plan.'}),
            'tipo_plan': forms.Select(attrs={'class': 'form-select w-full rounded-lg border-gray-300 shadow-sm'}),
            'imagen': forms.FileInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm'}),
        }
        labels = {
            'nombre': 'Nombre del Plan',
            'descripcion': 'Descripción',
            'tipo_plan': 'Tipo de Plan',
            'imagen': 'Imagen del Plan',
        }

class UnirseAForm(forms.Form):
    """Formulario para unirse a un plan grupal existente (usando ID o Código)."""
    codigo_plan = forms.IntegerField(
        label='ID del Plan',
        widget=forms.NumberInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ingresa el ID numérico del plan'})
    )

class EditPlanForm(forms.ModelForm):
    """Formulario para editar un Plan existente."""
    class Meta:
        model = Plan
        # Excluimos 'creador', 'fecha_creacion' y 'tipo_plan' ya que no se deben editar.
        fields = ['nombre', 'descripcion', 'imagen']

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ej: Viaje a Europa 2025'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-textarea w-full rounded-lg border-gray-300 shadow-sm', 'rows': 3, 'placeholder': 'Breve descripción del propósito del plan.'}),
            'imagen': forms.FileInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm'}),
        }
        labels = {
            'nombre': 'Nombre del Plan',
            'descripcion': 'Descripción',
            'imagen': 'Imagen del Plan',
        }

# ------------------------------
# 1. Formularios de FINANZAS
# ------------------------------

class IngresoForm(forms.ModelForm):
    """Formulario para registrar nuevos ingresos."""
    class Meta:
        model = Ingreso
        # Excluimos 'dinero' ya que se asigna automáticamente en la vista.
        # Excluimos 'fecha_guardado' ya que se asigna automáticamente en el modelo.
        fields = ['nombre', 'descripcion', 'tipo_ingreso', 'cantidad', 'imagen']

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ej: Salario de Septiembre'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-textarea w-full rounded-lg border-gray-300 shadow-sm', 'rows': 3, 'placeholder': 'Detalles adicionales (opcional)'}),
            'tipo_ingreso': forms.Select(attrs={'class': 'form-select w-full rounded-lg border-gray-300 shadow-sm'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Monto del ingreso', 'step': '0.01'}),
            'imagen': forms.FileInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm'}),
        }
        labels = {
            'nombre': 'Nombre del Ingreso',
            'descripcion': 'Descripción',
            'tipo_ingreso': 'Tipo',
            'cantidad': 'Cantidad ($)',
            'imagen': 'Imagen del Ingreso',
        }

class GastoForm(forms.ModelForm):
    """Formulario para registrar nuevos gastos."""
    class Meta:
        model = Gasto
        # Excluimos 'dinero' ya que se asigna automáticamente en la vista.
        # Excluimos 'fecha_guardado' ya que se asigna automáticamente en el modelo.
        fields = ['nombre', 'descripcion', 'tipo_gasto', 'cantidad', 'imagen']

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ej: Pago de alquiler'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-textarea w-full rounded-lg border-gray-300 shadow-sm', 'rows': 3, 'placeholder': 'Detalles de la transacción'}),
            'tipo_gasto': forms.Select(attrs={'class': 'form-select w-full rounded-lg border-gray-300 shadow-sm'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Monto del gasto', 'step': '0.01'}),
            'imagen': forms.FileInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm'}),
        }
        labels = {
            'nombre': 'Nombre del Gasto',
            'descripcion': 'Descripción',
            'tipo_gasto': 'Tipo',
            'cantidad': 'Cantidad ($)',
            'imagen': 'Imagen del Gasto',
        }

# ------------------------------
# 2. Formularios de PLANIFICACIÓN
# ------------------------------

class ObjetivoForm(forms.ModelForm):
    """Formulario para crear un nuevo objetivo de ahorro."""
    class Meta:
        model = Objetivo
        # Excluimos 'plan' y 'fecha_guardado' (asignados en la vista/modelo)
        # Excluimos 'monto_actual' y 'estado' (tienen valores por defecto)
        fields = ['nombre', 'detalles', 'monto_necesario', 'imagen']

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ej: Fondo de Emergencia'}),
            'detalles': forms.Textarea(attrs={'class': 'form-textarea w-full rounded-lg border-gray-300 shadow-sm', 'rows': 3, 'placeholder': 'Detalles y propósito del objetivo'}),
            'monto_necesario': forms.NumberInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Monto total requerido', 'step': '0.01'}),
            'imagen': forms.FileInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm'}),
        }
        labels = {
            'nombre': 'Nombre del Objetivo',
            'detalles': 'Detalles',
            'monto_necesario': 'Meta de Ahorro ($)',
            'imagen': 'Imagen del Objetivo',
        }
        
# Este formulario es un placeholder para cuando el usuario quiera aportar dinero
class AportarObjetivoForm(forms.Form):
    """Formulario para aportar dinero a un objetivo existente."""
    monto_aportar = forms.DecimalField(
        label='Monto a Aportar ($)', 
        max_digits=15, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Monto', 'step': '0.01'})
    )


class TareaForm(forms.ModelForm):
    """Formulario para crear una nueva tarea o recordatorio."""
    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)

        # Si hay un plan, mostrar solo los miembros del plan como opciones para asignar
        if self.plan:
            miembros = Suscripcion.objects.filter(plan=self.plan).select_related('usuario')
            choices = [(suscripcion.usuario.id, suscripcion.usuario.username) for suscripcion in miembros]
            # Agregar opción para no asignar a nadie
            choices.insert(0, ('', 'No asignar a nadie'))
            self.fields['usuario_asignado'].choices = choices

    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)

        # Si hay un plan, mostrar solo los miembros del plan como opciones para asignar
        if self.plan:
            miembros = Suscripcion.objects.filter(plan=self.plan).select_related('usuario')
            choices = [(suscripcion.usuario.id, suscripcion.usuario.username) for suscripcion in miembros]
            # Agregar opción para no asignar a nadie
            choices.insert(0, ('', 'No asignar a nadie'))
            self.fields['usuario_asignado'].choices = choices

    class Meta:
        model = Tarea
        # Excluimos 'plan' y 'fecha_guardado' (asignados en la vista/modelo)
        # Excluimos 'estado' y 'fecha_completado' (tienen valores por defecto)
        fields = ['nombre', 'descripcion', 'tipo_tarea', 'usuario_asignado', 'fecha_a_completar', 'imagen']

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'placeholder': 'Ej: Pagar la luz'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-textarea w-full rounded-lg border-gray-300 shadow-sm', 'rows': 2, 'placeholder': 'Descripción de la tarea (opcional)'}),
            'tipo_tarea': forms.Select(attrs={'class': 'form-select w-full rounded-lg border-gray-300 shadow-sm'}),
            'usuario_asignado': forms.Select(attrs={'class': 'form-select w-full rounded-lg border-gray-300 shadow-sm'}),
            'fecha_a_completar': forms.DateInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm', 'type': 'date'}),
            'imagen': forms.FileInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300 shadow-sm'}),
        }
        labels = {
            'nombre': 'Título de la Tarea',
            'descripcion': 'Descripción',
            'tipo_tarea': 'Tipo',
            'usuario_asignado': 'Asignar a (principal)',
            'fecha_a_completar': 'Fecha Límite',
            'imagen': 'Imagen de la Tarea',
        }


# EcoSmart - Nueva Estructura del Proyecto

## Estructura Propuesta

```
EcoSmart/
├── config/                    # Configuración del proyecto
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                      # Aplicaciones Django
│   ├── __init__.py
│   ├── core/                  # Funcionalidades básicas
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── forms.py
│   │   └── managers.py
│   ├── authentication/        # Autenticación y perfiles
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── forms.py
│   │   └── serializers.py
│   ├── financial_plans/       # Planes financieros
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── transactions/          # Transacciones (ingresos/gastos)
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── goals/                 # Objetivos financieros
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── tasks/                 # Tareas y recordatorios
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── forms.py
│   │   └── services.py
│   └── chatbot/              # Chatbot
│       ├── __init__.py
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── admin.py
│       ├── forms.py
│       └── services.py
├── static/                   # Archivos estáticos globales
│   ├── css/
│   │   ├── base.css
│   │   ├── components/
│   │   └── pages/
│   ├── js/
│   │   ├── base.js
│   │   └── components/
│   └── images/
├── templates/                # Templates globales
│   ├── base/
│   │   ├── base.html
│   │   └── components/
│   └── pages/
├── media/                    # Archivos subidos por usuarios
├── requirements/             # Dependencias
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── docs/                     # Documentación
│   ├── api.md
│   ├── deployment.md
│   └── development.md
├── scripts/                  # Scripts de utilidad
│   ├── setup.py
│   └── deploy.py
├── tests/                    # Tests globales
│   ├── __init__.py
│   ├── conftest.py
│   └── factories.py
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Principios de Organización

### 1. Separación por Responsabilidad
- **core**: Funcionalidades básicas compartidas
- **authentication**: Manejo de usuarios y perfiles
- **financial_plans**: Gestión de planes financieros
- **transactions**: Ingresos y gastos
- **goals**: Objetivos financieros
- **tasks**: Tareas y recordatorios
- **chatbot**: Funcionalidad de chatbot

### 2. Configuración Modular
- Settings separados por entorno
- Configuración centralizada en `config/`

### 3. Archivos Estáticos Organizados
- CSS/JS globales en `static/`
- Archivos específicos por app en `apps/[app]/static/`

### 4. Templates Jerárquicos
- Base templates en `templates/base/`
- Templates específicos por app

### 5. Servicios y Lógica de Negocio
- Cada app tiene su `services.py` para lógica compleja
- Separación clara entre views y lógica de negocio


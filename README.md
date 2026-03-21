# GymTracking

SaaS de seguimiento de entrenamiento de gimnasio. Mobile-first, multi-usuario con roles supervisor/atleta.

## Instalación rápida

```bash
# 1. Instalar dependencias
pip3 install Django Pillow

# 2. Aplicar migraciones
python3 manage.py migrate

# 3. Cargar datos de ejemplo (usuarios + ejercicios + plan + sesiones)
python3 manage.py shell < create_demo_data.py

# 4. Arrancar
python3 manage.py runserver
```

Abre http://127.0.0.1:8000

## Cuentas de ejemplo

| Usuario   | Contraseña | Rol        |
|-----------|------------|------------|
| `admin`   | `admin123` | Supervisor |
| `atleta1` | `atleta123`| Atleta     |

Admin de Django: http://127.0.0.1:8000/admin/

## Estructura del proyecto

```
gymtracking/     → Configuración Django (settings, urls)
users/           → Usuarios, roles (supervisor/atleta), autenticación
exercises/       → Catálogo de ejercicios (CRUD)
plans/           → Planes de entrenamiento semanales/mensuales
sessions/        → Registro de sesiones y series
reports/         → Dashboard, gráficas de progreso, resumen semanal
templates/       → Templates HTML (Tailwind CSS, mobile-first)
```

## Módulos

### Usuarios y roles
- **Supervisor**: ve datos de todos sus atletas asignados
- **Atleta**: ve solo sus propios datos

### Catálogo de ejercicios
- Nombre, descripción, grupos musculares, tipo (fuerza/cardio/flexibilidad)
- Imagen opcional, filtros por músculo y tipo

### Planes de entrenamiento
- Planes semanales o mensuales
- Ejercicios por día con series, repeticiones y peso objetivo
- Asignables a usuarios específicos

### Registro de sesiones
- Vista optimizada para móvil con botones grandes
- Registro rápido de series (AJAX sin recargar página)
- Vinculación con plan activo, estado de ánimo, notas

### Informes y evolución
- Dashboard con estadísticas (sesiones, volumen, racha)
- Gráfica de progreso por ejercicio (peso máximo y volumen)
- Resumen semanal comparado con el plan

## Migración a PostgreSQL

En `gymtracking/settings.py`, reemplazar el bloque `DATABASES` con:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gymtracking',
        'USER': 'postgres',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Luego: `pip install psycopg2-binary && python3 manage.py migrate`

## Stack técnico

- **Backend**: Django 4.2+ / Python 3.10+
- **Base de datos**: SQLite (dev) → PostgreSQL (prod)
- **CSS**: Tailwind CSS (CDN)
- **Gráficas**: Chart.js
- **Diseño**: Mobile-first, componentes del sistema de diseño COMPONENTES

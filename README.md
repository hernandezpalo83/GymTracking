# 🏋️ GymTracking

**Plataforma SaaS de seguimiento y planificación de entrenamientos de gimnasio.**
Mobile-first · Django 4.2 · Multi-usuario con roles · Informes de evolución

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)](https://djangoproject.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ✨ Características principales

- **Planificación semanal y mensual** — crea planes de entrenamiento con ejercicios, series, repeticiones y pesos objetivo. Los planes se pueden repetir automáticamente al siguiente período con un clic.
- **Registro de sesiones desde el móvil** — añade series con un toque, con pre-relleno automático de los valores de la última sesión. No es obligatorio tener un plan activo.
- **Catálogo de ejercicios** — diferencia entre fuerza (series/reps/peso) y cardio (tiempo/distancia/ritmo). Organizado por grupos musculares.
- **6 informes de evolución** — dashboard personal, progresión por ejercicio, cumplimiento de plan, músculos trabajados, historial de sesiones y panel de supervisión.
- **Sistema multi-usuario con roles** — superusuario, supervisor y atleta, con visibilidad de datos segmentada por rol.
- **Modo oscuro** — activable por usuario, preferencia guardada en perfil.
- **Diseño mobile-first** — optimizado para uso desde el teléfono durante el entrenamiento.

---

## 🏗️ Arquitectura

```
GymTracking/
├── gymtracking/          # Configuración Django (settings, urls, wsgi)
├── users/                # Autenticación, roles y gestión de perfiles
├── exercises/            # Catálogo de ejercicios y grupos musculares
├── plans/                # Planes de entrenamiento (semanales/mensuales)
├── sessions/             # Registro de sesiones y series realizadas
├── reports/              # Dashboard e informes de evolución
├── templates/            # Templates HTML mobile-first
├── static/               # CSS, JS, imágenes estáticas
├── fixtures/             # Datos de ejemplo para desarrollo
├── .github/workflows/    # CI/CD con GitHub Actions
├── arrancar.sh           # Script de arranque local interactivo
└── manage.py
```

---

## 👥 Roles de usuario

| Rol | Descripción |
|-----|-------------|
| **Superusuario** | Acceso total. CRUD de usuarios, ejercicios y planes. Puede marcar planes como generales (visibles para todos) o particulares. |
| **Supervisor** | Ve y gestiona los datos de sus atletas asignados. Crea planes visibles para sus atletas. |
| **Atleta** | Ve sus propios datos. Crea planes privados. Registra sus sesiones. |

---

## 🚀 Instalación local

### Requisitos

- Python 3.12+
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/hernandezpalo83/GymTracking.git
cd GymTracking

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 4. Aplicar migraciones
python manage.py migrate

# 5. Cargar datos de ejemplo (opcional)
python manage.py loaddata fixtures/*.json

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Arrancar el servidor
python manage.py runserver
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Script de arranque interactivo

Alternativamente, usa el script que guía todo el proceso:

```bash
chmod +x arrancar.sh
./arrancar.sh
```

---

## ⚙️ Variables de entorno

Copia `.env.example` a `.env` y configura los valores:

```env
DJANGO_SECRET_KEY=tu-clave-secreta-muy-larga
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

> ⚠️ El archivo `.env` está en `.gitignore` y nunca se sube al repositorio.

---

## 🗃️ Modelos principales

### `users.User`
Extiende `AbstractUser`. Campos adicionales: `role` (supervisor/athlete), `supervised_by` (FK a supervisor), `avatar`, `bio`, `dark_mode`.

### `exercises.Exercise`
- `name`, `description`, `exercise_type` (strength/cardio/flexibility)
- `muscle_groups` (M2M con `MuscleGroup`)
- `is_public`, `created_by`

### `exercises.MuscleGroup`
Grupos: pecho, espalda, piernas, hombros, bíceps, tríceps, core, cardio, glúteos, gemelos, antebrazos, cuerpo completo.

### `plans.TrainingPlan`
- `name`, `plan_type` (weekly/monthly), `start_date`, `end_date`
- `visibility` (general/supervisor/private), `assigned_to`, `created_by`
- Relación con `PlanDay` → `PlanExercise` (series/reps/peso objetivo)

### `sessions.TrainingSession`
- `user`, `date`, `plan` (opcional), `notes`, `mood`
- Relación con `SessionExercise` → `ExerciseSet` (reps reales, peso real, tiempo, distancia)

---

## 📊 Informes disponibles

| Informe | Descripción | Filtros |
|---------|-------------|---------|
| **Dashboard personal** | Resumen ejecutivo del período con comparativa | Usuario, período |
| **Progresión por ejercicio** | Evolución de peso, volumen y récords | Ejercicio, fechas, usuario |
| **Sesiones** | Historial con volumen y cumplimiento | Fechas, usuario, plan |
| **Cumplimiento de plan** | % ejercicios completados, vista calendario | Plan, usuario, período |
| **Músculos trabajados** | Frecuencia y volumen por grupo muscular | Fechas, usuario |
| **Supervisión** *(solo supervisor/admin)* | Tabla comparativa de atletas asignados | Supervisor, fechas |

---

## 🧪 Tests

```bash
python manage.py test
```

Los tests cubren modelos, vistas y permisos por rol en todas las apps.

---

## 🌐 Despliegue en producción (Koyeb)

### Variables de entorno en Koyeb

```env
DJANGO_SECRET_KEY=<clave-segura>
DEBUG=False
ALLOWED_HOSTS=<tu-app>.koyeb.app
DATABASE_URL=<postgresql-url-de-koyeb>
```

### CI/CD automático

Cada push a `main` ejecuta los tests y, si pasan, despliega automáticamente en Koyeb via GitHub Actions. Ver `.github/workflows/ci-cd.yml`.

### Archivos estáticos

Los archivos estáticos se sirven con [WhiteNoise](https://whitenoise.readthedocs.io). Antes del primer despliegue:

```bash
python manage.py collectstatic --noinput
```

---

## 🛠️ Stack tecnológico

| Categoría | Tecnología |
|-----------|------------|
| Backend | Django 4.2, Python 3.12 |
| Base de datos | SQLite (dev) / PostgreSQL (prod) |
| Autenticación | Django Auth + roles personalizados |
| Frontend | Tailwind CSS, Chart.js |
| Archivos estáticos | WhiteNoise |
| Servidor WSGI | Gunicorn |
| CI/CD | GitHub Actions |
| Hosting | Koyeb |
| BD producción | Koyeb PostgreSQL / Neon |

---

## 📁 Datos de ejemplo

Los fixtures incluyen ejercicios de muestra organizados por tipo y grupo muscular, listos para cargar con:

```bash
python manage.py loaddata fixtures/*.json
```

---

## 🔒 Seguridad

- CSRF en todos los formularios
- Control de acceso por rol en todas las vistas
- Variables sensibles en `.env`, nunca en el código
- `DEBUG=False` en producción
- HTTPS forzado en producción (`SECURE_SSL_REDIRECT`)
- Cookies de sesión y CSRF con flag `Secure`

---

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Add: descripción del cambio'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request

---

## 📄 Licencia

MIT License — ver [LICENSE](LICENSE) para más detalles.

---

*Desarrollado con Django · Desplegado en Koyeb · 2026*

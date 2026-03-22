"""
Comando de arranque para el despliegue en producción.

Ejecuta en orden y de forma idempotente:
  1. Migraciones de base de datos
  2. Creación del superusuario por defecto (si no existe)
  3. Carga de fixtures de ejercicios (solo si la tabla está vacía)
  4. Carga de fixtures de planes (solo si la tabla está vacía)

Uso en run_command de Koyeb / Heroku / Railway:
  bash -c "python manage.py bootstrap && gunicorn gymtracking.wsgi --log-file -"
"""

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Bootstrap de producción: migrate + superuser + fixtures (idempotente)'

    def handle(self, *args, **options):
        # ── 0. Reset DB (solo si RESET_DB=true en variables de entorno) ─────
        if os.environ.get('RESET_DB', '').lower() == 'true':
            self.stdout.write(self.style.WARNING('⚠️  RESET_DB=true detectado — limpiando base de datos...'))
            call_command('flush', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('  ✓ Base de datos vaciada'))

        # ── 1. Migraciones ──────────────────────────────────────────────────
        self.stdout.write('→ Aplicando migraciones...')
        call_command('migrate', '--noinput', verbosity=0)
        self.stdout.write(self.style.SUCCESS('  ✓ Migraciones aplicadas'))

        # ── 2. Superusuario ─────────────────────────────────────────────────
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('  · Superusuario ya existe, omitiendo.')
        else:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gymtracking.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin1234!')
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Superusuario "{username}" creado'))

        # ── 3. Fixture de ejercicios ─────────────────────────────────────────
        self._load_fixture_if_empty(
            app_label='exercises',
            model_name='Exercise',
            fixture='fixtures/exercises.json',
            label='ejercicios',
        )

        # ── 4. Fixture de planes ─────────────────────────────────────────────
        self._load_fixture_if_empty(
            app_label='plans',
            model_name='TrainingPlan',
            fixture='fixtures/plans.json',
            label='planes de entrenamiento',
        )

        self.stdout.write(self.style.SUCCESS('\n✓ Bootstrap completado. Iniciando servidor...\n'))

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _load_fixture_if_empty(self, app_label, model_name, fixture, label):
        from django.apps import apps
        Model = apps.get_model(app_label, model_name)

        if Model.objects.exists():
            count = Model.objects.count()
            self.stdout.write(f'  · {label.capitalize()} ya existen ({count} registros), omitiendo fixture.')
            return

        self.stdout.write(f'→ Cargando fixture de {label}...')
        try:
            call_command('loaddata', fixture, verbosity=0)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Fixture de {label} cargado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error al cargar fixture de {label}: {e}'))

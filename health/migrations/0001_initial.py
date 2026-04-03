from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sessions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(
                    choices=[('google_fit', 'Google Fit')],
                    default='google_fit', max_length=30, verbose_name='Proveedor'
                )),
                ('access_token', models.TextField(verbose_name='Token de acceso')),
                ('refresh_token', models.TextField(blank=True, verbose_name='Token de refresco')),
                ('token_expiry', models.DateTimeField(blank=True, null=True, verbose_name='Expiración del token')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='health_connection',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Conexión de salud',
                'verbose_name_plural': 'Conexiones de salud',
            },
        ),
        migrations.CreateModel(
            name='DailySteps',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Fecha')),
                ('steps', models.IntegerField(default=0, verbose_name='Pasos')),
                ('source', models.CharField(default='google_fit', max_length=30, verbose_name='Fuente')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_steps',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Pasos diarios',
                'verbose_name_plural': 'Pasos diarios',
                'ordering': ['-date'],
                'unique_together': {('user', 'date')},
            },
        ),
        migrations.CreateModel(
            name='HealthSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=30, verbose_name='Proveedor')),
                ('sync_type', models.CharField(
                    choices=[('workout', 'Entrenamiento'), ('steps_read', 'Lectura de pasos')],
                    max_length=20, verbose_name='Tipo'
                )),
                ('status', models.CharField(
                    choices=[('success', 'Éxito'), ('error', 'Error'), ('skipped', 'Omitido')],
                    max_length=20, verbose_name='Estado'
                )),
                ('error_message', models.TextField(blank=True, verbose_name='Error')),
                ('data', models.JSONField(blank=True, default=dict, verbose_name='Datos')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='health_sync_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
                ('session', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='sessions.workoutsession',
                    verbose_name='Sesión',
                )),
            ],
            options={
                'verbose_name': 'Registro de sincronización',
                'verbose_name_plural': 'Registros de sincronización',
                'ordering': ['-created_at'],
            },
        ),
    ]

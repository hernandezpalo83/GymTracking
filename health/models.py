from django.db import models
from django.utils import timezone


class HealthConnection(models.Model):
    """Stores OAuth2 tokens for a user's health service connection (e.g. Google Fit)."""

    PROVIDER_CHOICES = [
        ('google_fit', 'Google Fit'),
    ]

    user = models.OneToOneField(
        'users.User', on_delete=models.CASCADE,
        related_name='health_connection', verbose_name='Usuario'
    )
    provider = models.CharField(
        max_length=30, choices=PROVIDER_CHOICES, default='google_fit',
        verbose_name='Proveedor'
    )
    access_token = models.TextField(verbose_name='Token de acceso')
    refresh_token = models.TextField(blank=True, verbose_name='Token de refresco')
    token_expiry = models.DateTimeField(null=True, blank=True, verbose_name='Expiración del token')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conexión de salud'
        verbose_name_plural = 'Conexiones de salud'

    def __str__(self):
        return f"{self.user.username} – {self.get_provider_display()}"

    def is_token_expired(self):
        if not self.token_expiry:
            return False
        return timezone.now() >= self.token_expiry


class DailySteps(models.Model):
    """Caches daily step counts fetched from a health service."""

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='daily_steps', verbose_name='Usuario'
    )
    date = models.DateField(verbose_name='Fecha')
    steps = models.IntegerField(default=0, verbose_name='Pasos')
    source = models.CharField(max_length=30, default='google_fit', verbose_name='Fuente')

    class Meta:
        unique_together = ('user', 'date')
        verbose_name = 'Pasos diarios'
        verbose_name_plural = 'Pasos diarios'
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} – {self.date}: {self.steps} pasos"


class HealthSyncLog(models.Model):
    """Audit log for health service sync operations."""

    STATUS_CHOICES = [
        ('success', 'Éxito'),
        ('error', 'Error'),
        ('skipped', 'Omitido'),
    ]
    SYNC_TYPE_CHOICES = [
        ('workout', 'Entrenamiento'),
        ('steps_read', 'Lectura de pasos'),
    ]

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='health_sync_logs', verbose_name='Usuario'
    )
    session = models.ForeignKey(
        'sessions.WorkoutSession', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Sesión'
    )
    provider = models.CharField(max_length=30, verbose_name='Proveedor')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES, verbose_name='Tipo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Estado')
    error_message = models.TextField(blank=True, verbose_name='Error')
    data = models.JSONField(blank=True, default=dict, verbose_name='Datos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de sincronización'
        verbose_name_plural = 'Registros de sincronización'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} – {self.sync_type} – {self.status}"

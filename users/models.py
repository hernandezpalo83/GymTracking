from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_SUPERVISOR = 'supervisor'
    ROLE_ATHLETE = 'athlete'
    ROLE_CHOICES = [
        (ROLE_SUPERVISOR, 'Supervisor'),
        (ROLE_ATHLETE, 'Atleta'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ATHLETE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    supervised_by = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='athletes',
        limit_choices_to={'role': 'supervisor'}
    )
    dark_mode = models.BooleanField(default=False, verbose_name='Modo oscuro')
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Peso corporal (kg)'
    )

    @property
    def is_supervisor(self):
        return self.role == self.ROLE_SUPERVISOR

    @property
    def is_athlete(self):
        return self.role == self.ROLE_ATHLETE

    def get_role_label(self):
        if self.is_superuser:
            return 'Superusuario'
        return self.get_role_display()

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_label()})"


class BodyMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='body_metrics')
    date = models.DateField(verbose_name='Fecha')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Peso (kg)')
    body_fat_pct = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        verbose_name='% grasa corporal'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Métrica corporal'
        verbose_name_plural = 'Métricas corporales'
        ordering = ['-date']
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} — {self.date}: {self.weight_kg} kg"

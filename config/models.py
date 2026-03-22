from django.db import models


class SiteSettings(models.Model):
    registration_enabled = models.BooleanField(default=False, verbose_name='Permitir registro de usuarios')
    stripe_enabled = models.BooleanField(default=False, verbose_name='Activar pagos con Stripe')
    stripe_public_key = models.CharField(max_length=200, blank=True)
    stripe_secret_key = models.CharField(max_length=200, blank=True)
    stripe_price_id = models.CharField(max_length=200, blank=True, verbose_name='ID de precio en Stripe')
    free_trial_days = models.IntegerField(default=14, verbose_name='Días de prueba gratuita')

    class Meta:
        verbose_name = 'Configuración del sitio'
        verbose_name_plural = 'Configuración del sitio'

    def __str__(self):
        return 'Configuración del sitio'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

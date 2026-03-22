from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_enabled', models.BooleanField(default=False, verbose_name='Permitir registro de usuarios')),
                ('stripe_enabled', models.BooleanField(default=False, verbose_name='Activar pagos con Stripe')),
                ('stripe_public_key', models.CharField(blank=True, max_length=200)),
                ('stripe_secret_key', models.CharField(blank=True, max_length=200)),
                ('stripe_price_id', models.CharField(blank=True, max_length=200, verbose_name='ID de precio en Stripe')),
                ('free_trial_days', models.IntegerField(default=14, verbose_name='Días de prueba gratuita')),
            ],
            options={
                'verbose_name': 'Configuración del sitio',
                'verbose_name_plural': 'Configuración del sitio',
            },
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='equipment',
            field=models.CharField(
                blank=True,
                choices=[
                    ('machine', 'Máquina'),
                    ('pulley', 'Polea'),
                    ('weights', 'Pesas libres'),
                    ('home', 'En casa / Sin material'),
                    ('bodyweight', 'Peso corporal'),
                    ('cardio_machine', 'Máquina cardio'),
                ],
                max_length=20,
                verbose_name='Material/Equipo',
            ),
        ),
    ]

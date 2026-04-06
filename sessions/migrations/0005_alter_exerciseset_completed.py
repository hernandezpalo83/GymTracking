# Generated migration to fix ExerciseSet completed default value

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout_sessions', '0004_sessionexercise_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exerciseset',
            name='completed',
            field=models.BooleanField(default=False, verbose_name='Completada'),
        ),
    ]

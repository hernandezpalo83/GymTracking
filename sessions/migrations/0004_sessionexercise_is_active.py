# Generated migration to add is_active field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout_sessions', '0003_personalrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='sessionexercise',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Es activo'),
        ),
    ]

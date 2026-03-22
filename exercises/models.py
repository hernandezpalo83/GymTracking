from django.db import models


class MuscleGroup(models.Model):
    CHOICES = [
        ('chest', 'Pecho'),
        ('back', 'Espalda'),
        ('legs', 'Piernas'),
        ('shoulders', 'Hombros'),
        ('biceps', 'Bíceps'),
        ('triceps', 'Tríceps'),
        ('core', 'Core/Abdomen'),
        ('cardio', 'Cardio'),
        ('glutes', 'Glúteos'),
        ('calves', 'Gemelos'),
        ('forearms', 'Antebrazos'),
        ('full_body', 'Cuerpo completo'),
    ]
    name = models.CharField(max_length=50, choices=CHOICES, unique=True)

    class Meta:
        verbose_name = 'Grupo muscular'
        verbose_name_plural = 'Grupos musculares'

    def __str__(self):
        return self.get_name_display()


class Exercise(models.Model):
    TYPE_CHOICES = [
        ('strength', 'Fuerza'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibilidad'),
    ]
    EQUIPMENT_CHOICES = [
        ('machine', 'Máquina'),
        ('pulley', 'Polea'),
        ('weights', 'Pesas libres'),
        ('home', 'En casa / Sin material'),
        ('bodyweight', 'Peso corporal'),
        ('cardio_machine', 'Máquina cardio'),
    ]
    name = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    muscle_groups = models.ManyToManyField(MuscleGroup, related_name='exercises', verbose_name='Grupos musculares')
    exercise_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='strength', verbose_name='Tipo')
    equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, blank=True, verbose_name='Material/Equipo')
    image = models.ImageField(upload_to='exercises/', blank=True, null=True, verbose_name='Imagen')
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_exercises'
    )
    is_public = models.BooleanField(default=True, verbose_name='Público')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ejercicio'
        verbose_name_plural = 'Ejercicios'
        ordering = ['name']

    def __str__(self):
        return self.name

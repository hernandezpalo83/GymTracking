from django.db import models


class TrainingPlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]
    DAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    VISIBILITY_GENERAL = 'general'
    VISIBILITY_PARTICULAR = 'particular'
    VISIBILITY_PERSONAL = 'personal'
    VISIBILITY_CHOICES = [
        ('general', 'General (visible para todos)'),
        ('particular', 'Particular (solo para el asignado)'),
        ('personal', 'Personal (solo para mí)'),
    ]

    name = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='weekly', verbose_name='Tipo')
    visibility = models.CharField(
        max_length=20, choices=VISIBILITY_CHOICES, default='particular',
        verbose_name='Visibilidad'
    )
    assigned_to = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='training_plans', verbose_name='Asignado a',
        null=True, blank=True
    )
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='created_plans', verbose_name='Creado por'
    )
    start_date = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    end_date = models.DateField(null=True, blank=True, verbose_name='Fecha de fin')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plan de entrenamiento'
        verbose_name_plural = 'Planes de entrenamiento'
        ordering = ['-created_at']

    def __str__(self):
        if self.assigned_to:
            return f"{self.name} - {self.assigned_to}"
        return self.name

    def get_exercises_by_day(self):
        """Return a dict with day number as key and list of exercises as value."""
        result = {day: [] for day, _ in self.DAY_CHOICES}
        for plan_exercise in self.plan_exercises.select_related('exercise').all():
            result[plan_exercise.day_of_week].append(plan_exercise)
        return result


class PlanExercise(models.Model):
    plan = models.ForeignKey(
        TrainingPlan, on_delete=models.CASCADE,
        related_name='plan_exercises'
    )
    exercise = models.ForeignKey(
        'exercises.Exercise', on_delete=models.CASCADE,
        verbose_name='Ejercicio'
    )
    day_of_week = models.IntegerField(choices=TrainingPlan.DAY_CHOICES, verbose_name='Día')
    sets = models.IntegerField(default=3, verbose_name='Series')
    reps = models.IntegerField(default=10, verbose_name='Repeticiones')
    target_weight = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True, verbose_name='Peso objetivo (kg)'
    )
    rest_seconds = models.IntegerField(default=60, verbose_name='Descanso (seg)')
    notes = models.TextField(blank=True, verbose_name='Notas')
    order = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        ordering = ['day_of_week', 'order']
        verbose_name = 'Ejercicio del plan'
        verbose_name_plural = 'Ejercicios del plan'

    def __str__(self):
        return f"{self.exercise.name} - Día {self.get_day_of_week_display()}"

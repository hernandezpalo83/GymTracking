from django.db import models


class WorkoutSession(models.Model):
    MOOD_CHOICES = [
        (1, 'Malo'),
        (2, 'Regular'),
        (3, 'Bueno'),
        (4, 'Muy bueno'),
        (5, 'Excelente'),
    ]

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='sessions', verbose_name='Usuario'
    )
    plan = models.ForeignKey(
        'plans.TrainingPlan', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sessions',
        verbose_name='Plan de entrenamiento'
    )
    date = models.DateField(verbose_name='Fecha')
    start_time = models.TimeField(null=True, blank=True, verbose_name='Hora inicio')
    end_time = models.TimeField(null=True, blank=True, verbose_name='Hora fin')
    notes = models.TextField(blank=True, verbose_name='Notas')
    mood = models.IntegerField(
        choices=MOOD_CHOICES, null=True, blank=True, verbose_name='Estado de ánimo'
    )
    completed = models.BooleanField(default=False, verbose_name='Completada')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sesión de entrenamiento'
        verbose_name_plural = 'Sesiones de entrenamiento'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Sesión {self.user} - {self.date}"

    def get_duration_minutes(self):
        if self.start_time and self.end_time:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            delta = end - start
            return int(delta.total_seconds() / 60)
        return None

    def get_total_volume(self):
        """Total volume in kg (weight * reps for all sets)."""
        total = 0
        for session_exercise in self.session_exercises.prefetch_related('sets').all():
            for exercise_set in session_exercise.sets.all():
                if exercise_set.weight and exercise_set.reps:
                    total += float(exercise_set.weight) * exercise_set.reps
        return total

    def get_mood_emoji(self):
        emojis = {1: '😞', 2: '😐', 3: '🙂', 4: '😊', 5: '😄'}
        return emojis.get(self.mood, '')


class SessionExercise(models.Model):
    session = models.ForeignKey(
        WorkoutSession, on_delete=models.CASCADE,
        related_name='session_exercises'
    )
    exercise = models.ForeignKey(
        'exercises.Exercise', on_delete=models.CASCADE,
        verbose_name='Ejercicio'
    )
    sets_completed = models.IntegerField(default=0, verbose_name='Series completadas')
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Ejercicio de sesión'
        verbose_name_plural = 'Ejercicios de sesión'

    def __str__(self):
        return f"{self.exercise.name}"


class ExerciseSet(models.Model):
    session_exercise = models.ForeignKey(
        SessionExercise, on_delete=models.CASCADE,
        related_name='sets'
    )
    set_number = models.IntegerField(verbose_name='Número de serie')
    # Strength fields
    reps = models.IntegerField(null=True, blank=True, verbose_name='Repeticiones')
    weight = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name='Peso (kg)'
    )
    # Cardio fields
    duration_seconds = models.IntegerField(null=True, blank=True, verbose_name='Duración (seg)')
    distance_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name='Distancia (m)'
    )
    completed = models.BooleanField(default=True, verbose_name='Completada')
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        ordering = ['set_number']
        verbose_name = 'Serie'
        verbose_name_plural = 'Series'

    def get_volume(self):
        """Volume for this set: reps × weight. Returns None for cardio sets."""
        if self.reps is not None and self.weight is not None:
            return float(self.weight) * self.reps
        return None

    def get_pace_display(self):
        """Pace (min/km) for cardio sets. Returns formatted string or None."""
        if self.duration_seconds and self.distance_meters and float(self.distance_meters) > 0:
            pace_sec_per_km = self.duration_seconds / (float(self.distance_meters) / 1000)
            mins = int(pace_sec_per_km // 60)
            secs = int(pace_sec_per_km % 60)
            return f"{mins}:{secs:02d} min/km"
        return None

    def get_duration_display(self):
        """Human-readable duration for cardio sets."""
        if self.duration_seconds is None:
            return None
        mins = self.duration_seconds // 60
        secs = self.duration_seconds % 60
        if mins:
            return f"{mins}m {secs:02d}s" if secs else f"{mins}m"
        return f"{secs}s"

    def __str__(self):
        return f"Serie {self.set_number}: {self.reps} x {self.weight}kg"

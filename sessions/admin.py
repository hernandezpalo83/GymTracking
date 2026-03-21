from django.contrib import admin
from .models import WorkoutSession, SessionExercise, ExerciseSet


class ExerciseSetInline(admin.TabularInline):
    model = ExerciseSet
    extra = 0
    fields = ('set_number', 'reps', 'weight', 'completed')


class SessionExerciseInline(admin.TabularInline):
    model = SessionExercise
    extra = 0
    fields = ('exercise', 'sets_completed', 'notes')


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'plan', 'mood', 'completed', 'created_at')
    list_filter = ('completed', 'mood', 'date')
    search_fields = ('user__username', 'user__email', 'notes')
    inlines = [SessionExerciseInline]
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'


@admin.register(SessionExercise)
class SessionExerciseAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'session', 'sets_completed')
    search_fields = ('exercise__name',)
    inlines = [ExerciseSetInline]


@admin.register(ExerciseSet)
class ExerciseSetAdmin(admin.ModelAdmin):
    list_display = ('session_exercise', 'set_number', 'reps', 'weight', 'completed')
    list_filter = ('completed',)

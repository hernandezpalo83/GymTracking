from django.contrib import admin
from .models import Exercise, MuscleGroup


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_name_display')
    search_fields = ('name',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'exercise_type', 'is_public', 'created_by', 'created_at')
    list_filter = ('exercise_type', 'is_public', 'muscle_groups')
    search_fields = ('name', 'description')
    filter_horizontal = ('muscle_groups',)
    readonly_fields = ('created_at',)

from django.contrib import admin
from .models import TrainingPlan, PlanExercise


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 0
    fields = ('exercise', 'day_of_week', 'sets', 'reps', 'target_weight', 'rest_seconds', 'order')


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'assigned_to', 'created_by', 'is_active', 'created_at')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name', 'description', 'assigned_to__username', 'assigned_to__email')
    inlines = [PlanExerciseInline]
    readonly_fields = ('created_at',)


@admin.register(PlanExercise)
class PlanExerciseAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'plan', 'day_of_week', 'sets', 'reps', 'target_weight')
    list_filter = ('day_of_week',)
    search_fields = ('exercise__name', 'plan__name')

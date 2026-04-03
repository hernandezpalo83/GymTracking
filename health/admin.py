from django.contrib import admin
from .models import HealthConnection, DailySteps, HealthSyncLog


@admin.register(HealthConnection)
class HealthConnectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'provider', 'token_expiry', 'updated_at']
    list_filter = ['provider']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']


@admin.register(DailySteps)
class DailyStepsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'steps', 'source']
    list_filter = ['source']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(HealthSyncLog)
class HealthSyncLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'sync_type', 'status', 'provider', 'created_at']
    list_filter = ['sync_type', 'status', 'provider']
    readonly_fields = ['created_at']
    search_fields = ['user__username']

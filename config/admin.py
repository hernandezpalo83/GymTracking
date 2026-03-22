from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Registro', {'fields': ('registration_enabled',)}),
        ('Stripe', {'fields': ('stripe_enabled', 'stripe_public_key', 'stripe_secret_key', 'stripe_price_id', 'free_trial_days')}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

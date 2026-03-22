from django import forms
from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'registration_enabled',
            'stripe_enabled',
            'stripe_public_key',
            'stripe_secret_key',
            'stripe_price_id',
            'free_trial_days',
        ]
        widgets = {
            'stripe_public_key': forms.TextInput(attrs={'class': 'block w-full rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500'}),
            'stripe_secret_key': forms.TextInput(attrs={'class': 'block w-full rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500'}),
            'stripe_price_id': forms.TextInput(attrs={'class': 'block w-full rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500'}),
            'free_trial_days': forms.NumberInput(attrs={'class': 'block w-full rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500'}),
        }

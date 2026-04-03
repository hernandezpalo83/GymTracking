from django import forms
from .models import Exercise, MuscleGroup


class ExerciseForm(forms.ModelForm):
    muscle_groups = forms.ModelMultipleChoiceField(
        queryset=MuscleGroup.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-1'}),
        required=False,
        label='Grupos musculares'
    )

    INPUT_CLASS = 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3'

    class Meta:
        model = Exercise
        fields = ('name', 'description', 'muscle_groups', 'exercise_type', 'image', 'video_url', 'met_value', 'rest_time', 'is_public')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3',
                'placeholder': 'Nombre del ejercicio'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3',
                'rows': 4,
                'placeholder': 'Descripción del ejercicio...'
            }),
            'exercise_type': forms.Select(attrs={
                'class': 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3',
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'met_value': forms.NumberInput(attrs={
                'class': 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3',
                'placeholder': 'ej. 5.0 (fuerza), 8.0 (carrera)',
                'step': '0.5', 'min': '1',
            }),
            'rest_time': forms.NumberInput(attrs={
                'class': 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3',
                'placeholder': 'ej. 30, 60, 90 segundos',
                'min': '5',
                'max': '300',
                'step': '5',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-5 w-5',
            }),
        }

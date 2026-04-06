from django import forms
from .models import WorkoutSession, SessionExercise, ExerciseSet
from exercises.models import Exercise

INPUT_CLASS = 'block w-full rounded-xl border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3'


class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ('date', 'plan', 'start_time', 'end_time', 'notes', 'mood')
        widgets = {
            'date': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'plan': forms.Select(attrs={'class': INPUT_CLASS}),
            'start_time': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time'}),
            'notes': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'rows': 3,
                'placeholder': 'Notas de la sesión (opcional)...'
            }),
            'mood': forms.Select(attrs={'class': INPUT_CLASS}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            from plans.models import TrainingPlan
            self.fields['plan'].queryset = TrainingPlan.objects.filter(
                assigned_to=user, is_active=True
            )
        # Plan is always optional — no plan required
        self.fields['plan'].required = False
        self.fields['plan'].empty_label = 'Sin plan (sesión libre)'
        self.fields['mood'].required = False
        self.fields['mood'].empty_label = 'Seleccionar estado de ánimo...'
        self.fields['start_time'].required = False
        self.fields['end_time'].required = False
        self.fields['notes'].required = False


class SessionExerciseForm(forms.ModelForm):
    class Meta:
        model = SessionExercise
        fields = ('exercise', 'notes')
        widgets = {
            'exercise': forms.Select(attrs={'class': INPUT_CLASS}),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show public exercises
        self.fields['exercise'].queryset = Exercise.objects.filter(is_public=True)
        # Make notes optional
        self.fields['notes'].required = False


class ExerciseSetForm(forms.ModelForm):
    class Meta:
        model = ExerciseSet
        fields = ('set_number', 'reps', 'weight', 'completed', 'notes')
        widgets = {
            'set_number': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 1}),
            'reps': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'weight': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.5', 'min': 0}),
            'completed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-5 w-5'
            }),
            'notes': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }

from django import forms
from .models import TrainingPlan, PlanExercise
from users.models import User
from exercises.models import Exercise

INPUT_CLASS = 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3'


class TrainingPlanForm(forms.ModelForm):
    class Meta:
        model = TrainingPlan
        fields = ('name', 'description', 'plan_type', 'visibility', 'assigned_to', 'start_date', 'end_date', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Nombre del plan'
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'rows': 3,
            }),
            'plan_type': forms.Select(attrs={'class': INPUT_CLASS}),
            'visibility': forms.Select(attrs={'class': INPUT_CLASS}),
            'assigned_to': forms.Select(attrs={'class': INPUT_CLASS}),
            'start_date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-5 w-5',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user and user.is_superuser:
            # Superuser can assign to anyone
            self.fields['assigned_to'].queryset = User.objects.all()
            self.fields['assigned_to'].required = False
        elif user and user.is_supervisor:
            # Supervisor: assign to their athletes only
            self.fields['assigned_to'].queryset = User.objects.filter(supervised_by=user)
            self.fields['assigned_to'].required = False
            # Supervisors can only create 'particular' or 'personal' plans
            self.fields['visibility'].choices = [
                ('particular', 'Particular (solo para el asignado)'),
                ('personal', 'Personal (solo para mí)'),
            ]
        elif user:
            # Athlete: assign to themselves only
            self.fields['assigned_to'].queryset = User.objects.filter(pk=user.pk)
            self.fields['assigned_to'].initial = user
            self.fields['assigned_to'].required = False
            # Athletes can only create personal plans
            self.fields['visibility'].choices = [
                ('personal', 'Personal (solo para mí)'),
            ]
            self.fields['visibility'].initial = 'personal'


class PlanExerciseForm(forms.ModelForm):
    class Meta:
        model = PlanExercise
        fields = ('exercise', 'day_of_week', 'sets', 'reps', 'target_weight', 'rest_seconds', 'notes', 'order')
        widgets = {
            'exercise': forms.Select(attrs={'class': INPUT_CLASS}),
            'day_of_week': forms.Select(attrs={'class': INPUT_CLASS}),
            'sets': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 1, 'max': 20}),
            'reps': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 1, 'max': 100}),
            'target_weight': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.5'}),
            'rest_seconds': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 2}),
            'order': forms.NumberInput(attrs={'class': INPUT_CLASS}),
        }

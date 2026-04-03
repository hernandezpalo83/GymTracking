"""
Formularios para los filtros de reportes
"""

from django import forms
from exercises.models import Exercise, MuscleGroup


PERIOD_CHOICES = [
    ('week', 'Última semana'),
    ('month', 'Último mes'),
    ('90d', 'Últimos 90 días'),
    ('year', 'Último año'),
    ('custom', 'Personalizado'),
]

EXERCISE_TYPE_CHOICES = [
    ('', 'Todos'),
    ('strength', 'Fuerza'),
    ('cardio', 'Cardio'),
    ('flexibility', 'Flexibilidad'),
]


class ReportFilterForm(forms.Form):
    """Formulario base para filtros de reportes"""

    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        initial='month',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Período'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        label='Desde'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        label='Hasta'
    )


class ProgressFilterForm(ReportFilterForm):
    """Filtros para informe de Progreso Personal"""

    exercise_type = forms.ChoiceField(
        choices=EXERCISE_TYPE_CHOICES,
        required=False,
        initial='',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Ejercicio'
    )

    muscle_group = forms.ModelChoiceField(
        queryset=MuscleGroup.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Grupo Muscular (opcional)'
    )


class ExerciseFilterForm(ReportFilterForm):
    """Filtros para informe Por Ejercicio"""

    exercise_type = forms.ChoiceField(
        choices=EXERCISE_TYPE_CHOICES,
        required=False,
        initial='',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Ejercicio'
    )


class TypeFilterForm(ReportFilterForm):
    """Filtros para informe Por Tipo de Ejercicio"""

    exercise_type = forms.ChoiceField(
        choices=EXERCISE_TYPE_CHOICES[1:],  # Sin "Todos"
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Ejercicio'
    )

    muscle_group = forms.ModelChoiceField(
        queryset=MuscleGroup.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Grupo Muscular (opcional)'
    )


class MuscleFilterForm(ReportFilterForm):
    """Filtros para informe Por Grupo Muscular"""

    muscle_group = forms.ModelChoiceField(
        queryset=MuscleGroup.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Grupo Muscular',
        required=False
    )

    show_alert = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Mostrar alerta de balance'
    )


class ConsistencyFilterForm(forms.Form):
    """Filtros para informe de Consistencia"""

    weeks = forms.IntegerField(
        initial=4,
        min_value=1,
        max_value=52,
        widget=forms.NumberInput(attrs={'class': 'form-input'}),
        label='Semanas a mostrar'
    )

    show_heatmap = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Mostrar heatmap'
    )


class PerformanceFilterForm(ReportFilterForm):
    """Filtros para informe de Rendimiento"""

    compare_previous = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        label='Comparar con período anterior'
    )

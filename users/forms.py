from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, BodyMetric


INPUT_CLASS = 'block w-full rounded-xl border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 px-4 py-3'


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'tu@email.com'
    }))
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'Tu nombre'
    }))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'Tu apellido'
    }))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={
        'class': INPUT_CLASS,
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'nombre_usuario'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['password1', 'password2']:
            self.fields[field_name].widget.attrs.update({'class': INPUT_CLASS})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'bio', 'avatar', 'weight_kg')
        widgets = {
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'bio': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            'weight_kg': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'ej. 75.5', 'step': '0.5', 'min': '30', 'max': '300'
            }),
        }


class BodyMetricForm(forms.ModelForm):
    class Meta:
        model = BodyMetric
        fields = ('date', 'weight_kg', 'body_fat_pct', 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'weight_kg': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'ej. 75.5', 'step': '0.1', 'min': '30'
            }),
            'body_fat_pct': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'ej. 18.5', 'step': '0.1', 'min': '3', 'max': '60'
            }),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 2, 'placeholder': 'Notas opcionales...'}),
        }


class AdminUserCreateForm(UserCreationForm):
    """Form for superuser to create new users with all fields."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': INPUT_CLASS, 'placeholder': 'usuario@email.com'
    }))
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS
    }))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role',
                  'supervised_by', 'is_active', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'role': forms.Select(attrs={'class': INPUT_CLASS}),
            'supervised_by': forms.Select(attrs={'class': INPUT_CLASS}),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-5 w-5'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['password1', 'password2']:
            self.fields[field_name].widget.attrs.update({'class': INPUT_CLASS})
        self.fields['supervised_by'].queryset = User.objects.filter(role=User.ROLE_SUPERVISOR)
        self.fields['supervised_by'].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class AdminUserEditForm(forms.ModelForm):
    """Form for superuser to edit existing users."""
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role',
                  'supervised_by', 'is_active', 'bio')
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'role': forms.Select(attrs={'class': INPUT_CLASS}),
            'supervised_by': forms.Select(attrs={'class': INPUT_CLASS}),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-5 w-5'
            }),
            'bio': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervised_by'].queryset = User.objects.filter(role=User.ROLE_SUPERVISOR)
        self.fields['supervised_by'].required = False

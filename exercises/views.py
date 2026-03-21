from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

from .models import Exercise, MuscleGroup
from .forms import ExerciseForm


class ExerciseListView(LoginRequiredMixin, ListView):
    model = Exercise
    template_name = 'exercises/list.html'
    context_object_name = 'exercises'
    paginate_by = 12

    def get_queryset(self):
        queryset = Exercise.objects.filter(
            Q(is_public=True) | Q(created_by=self.request.user)
        ).prefetch_related('muscle_groups')

        muscle_group = self.request.GET.get('muscle_group')
        if muscle_group:
            queryset = queryset.filter(muscle_groups__name=muscle_group)

        exercise_type = self.request.GET.get('type')
        if exercise_type:
            queryset = queryset.filter(exercise_type=exercise_type)

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['muscle_groups'] = MuscleGroup.objects.all()
        context['type_choices'] = Exercise.TYPE_CHOICES
        context['current_muscle_group'] = self.request.GET.get('muscle_group', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ExerciseDetailView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = 'exercises/detail.html'
    context_object_name = 'exercise'


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin that restricts access to superusers only."""
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'Solo los superusuarios pueden crear, editar o eliminar ejercicios.')
        return redirect('exercises:list')


class ExerciseCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'exercises/form.html'
    success_url = reverse_lazy('exercises:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Ejercicio creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Ejercicio'
        context['submit_text'] = 'Crear Ejercicio'
        return context


class ExerciseUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'exercises/form.html'

    def get_success_url(self):
        return reverse_lazy('exercises:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Ejercicio actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Ejercicio'
        context['submit_text'] = 'Guardar Cambios'
        return context


class ExerciseDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = Exercise
    template_name = 'exercises/confirm_delete.html'
    success_url = reverse_lazy('exercises:list')

    def form_valid(self, form):
        messages.success(self.request, 'Ejercicio eliminado correctamente.')
        return super().form_valid(form)

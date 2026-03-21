from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from datetime import date, timedelta
import calendar

from .models import TrainingPlan, PlanExercise
from .forms import TrainingPlanForm, PlanExerciseForm


def _week_dates(today=None):
    """Return (monday, sunday) of the current week."""
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def _month_dates(today=None):
    """Return (first_day, last_day) of the current month."""
    today = today or date.today()
    first = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    return first, today.replace(day=last_day)


class PlanListView(LoginRequiredMixin, ListView):
    model = TrainingPlan
    template_name = 'plans/list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TrainingPlan.objects.all().select_related('assigned_to', 'created_by')
        elif user.is_supervisor:
            # See: general plans + plans for their athletes + their own created plans
            return TrainingPlan.objects.filter(
                Q(visibility='general') |
                Q(assigned_to__supervised_by=user) |
                Q(created_by=user)
            ).select_related('assigned_to', 'created_by').distinct()
        else:
            # Athlete: see general plans + plans assigned to them
            return TrainingPlan.objects.filter(
                Q(visibility='general') |
                Q(assigned_to=user)
            ).select_related('assigned_to', 'created_by').distinct()


class PlanDetailView(LoginRequiredMixin, DetailView):
    model = TrainingPlan
    template_name = 'plans/detail.html'
    context_object_name = 'plan'

    def get_object(self, queryset=None):
        plan = super().get_object(queryset)
        user = self.request.user
        # Security: only allow access if user has rights to this plan
        if user.is_superuser:
            return plan
        if plan.visibility == 'general':
            return plan
        if plan.assigned_to == user or plan.created_by == user:
            return plan
        if user.is_supervisor and plan.assigned_to and plan.assigned_to.supervised_by == user:
            return plan
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        context['exercises_by_day'] = plan.get_exercises_by_day()
        context['day_choices'] = TrainingPlan.DAY_CHOICES
        context['add_exercise_form'] = PlanExerciseForm()
        return context


class PlanCreateView(LoginRequiredMixin, CreateView):
    model = TrainingPlan
    form_class = TrainingPlanForm
    template_name = 'plans/form.html'
    success_url = reverse_lazy('plans:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # If athlete and no assigned_to, assign to themselves
        if not form.instance.assigned_to and not self.request.user.is_superuser:
            form.instance.assigned_to = self.request.user
        messages.success(self.request, 'Plan de entrenamiento creado correctamente.')
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        monday, sunday = _week_dates()
        first, last = _month_dates()
        initial['start_date'] = monday
        initial['end_date'] = sunday
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Plan de Entrenamiento'
        context['submit_text'] = 'Crear Plan'
        monday, sunday = _week_dates()
        first, last = _month_dates()
        context['weekly_start'] = monday.isoformat()
        context['weekly_end'] = sunday.isoformat()
        context['monthly_start'] = first.isoformat()
        context['monthly_end'] = last.isoformat()
        return context


class PlanUpdateView(LoginRequiredMixin, UpdateView):
    model = TrainingPlan
    form_class = TrainingPlanForm
    template_name = 'plans/form.html'

    def get_object(self, queryset=None):
        plan = super().get_object(queryset)
        user = self.request.user
        if not user.is_superuser and plan.created_by != user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return plan

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('plans:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Plan actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Plan'
        context['submit_text'] = 'Guardar Cambios'
        return context


class PlanDeleteView(LoginRequiredMixin, DeleteView):
    model = TrainingPlan
    template_name = 'plans/confirm_delete.html'
    success_url = reverse_lazy('plans:list')

    def get_object(self, queryset=None):
        plan = super().get_object(queryset)
        user = self.request.user
        if not user.is_superuser and plan.created_by != user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return plan

    def form_valid(self, form):
        messages.success(self.request, 'Plan eliminado correctamente.')
        return super().form_valid(form)


@login_required
def add_exercise_to_plan(request, plan_pk):
    plan = get_object_or_404(TrainingPlan, pk=plan_pk)

    # Only plan creator or superuser can add exercises
    if not request.user.is_superuser and plan.created_by != request.user:
        messages.error(request, 'No tienes permisos para modificar este plan.')
        return redirect('plans:detail', pk=plan_pk)

    if request.method == 'POST':
        form = PlanExerciseForm(request.POST)
        if form.is_valid():
            plan_exercise = form.save(commit=False)
            plan_exercise.plan = plan
            plan_exercise.save()
            messages.success(request, 'Ejercicio añadido al plan.')
        else:
            messages.error(request, 'Error al añadir ejercicio.')

    return redirect('plans:detail', pk=plan_pk)


@login_required
def remove_exercise_from_plan(request, plan_pk, exercise_pk):
    plan = get_object_or_404(TrainingPlan, pk=plan_pk)
    plan_exercise = get_object_or_404(PlanExercise, pk=exercise_pk, plan=plan)

    if not request.user.is_superuser and plan.created_by != request.user:
        messages.error(request, 'No tienes permisos para modificar este plan.')
        return redirect('plans:detail', pk=plan_pk)

    if request.method == 'POST':
        plan_exercise.delete()
        messages.success(request, 'Ejercicio eliminado del plan.')

    return redirect('plans:detail', pk=plan_pk)


@login_required
def repeat_plan(request, plan_pk):
    """Create a copy of a plan for the next week or month."""
    plan = get_object_or_404(TrainingPlan, pk=plan_pk)

    if not request.user.is_superuser and plan.created_by != request.user:
        messages.error(request, 'No tienes permisos para repetir este plan.')
        return redirect('plans:detail', pk=plan_pk)

    if request.method == 'POST':
        today = date.today()

        if plan.plan_type == 'weekly':
            # Next week's Monday–Sunday
            if plan.end_date and plan.end_date >= today:
                # If plan hasn't ended, start after its end date
                next_start = plan.end_date + timedelta(days=1)
            else:
                monday, _ = _week_dates(today)
                next_start = monday
            # Ensure it starts on Monday
            days_to_monday = (7 - next_start.weekday()) % 7
            next_start = next_start + timedelta(days=days_to_monday) if days_to_monday else next_start
            next_end = next_start + timedelta(days=6)
        else:
            # Next month
            if plan.end_date and plan.end_date >= today:
                next_month = plan.end_date.replace(day=1) + timedelta(days=32)
            else:
                next_month = today.replace(day=1) + timedelta(days=32)
            next_start = next_month.replace(day=1)
            last_day = calendar.monthrange(next_start.year, next_start.month)[1]
            next_end = next_start.replace(day=last_day)

        new_plan = TrainingPlan.objects.create(
            name=plan.name,
            description=plan.description,
            plan_type=plan.plan_type,
            visibility=plan.visibility,
            assigned_to=plan.assigned_to,
            created_by=request.user,
            start_date=next_start,
            end_date=next_end,
            is_active=True,
        )

        # Copy exercises
        for pe in plan.plan_exercises.all():
            PlanExercise.objects.create(
                plan=new_plan,
                exercise=pe.exercise,
                day_of_week=pe.day_of_week,
                sets=pe.sets,
                reps=pe.reps,
                target_weight=pe.target_weight,
                rest_seconds=pe.rest_seconds,
                notes=pe.notes,
                order=pe.order,
            )

        messages.success(request, f'Plan repetido correctamente para el período {next_start.strftime("%d/%m/%Y")} – {next_end.strftime("%d/%m/%Y")}.')
        return redirect('plans:detail', pk=new_plan.pk)

    return redirect('plans:detail', pk=plan_pk)

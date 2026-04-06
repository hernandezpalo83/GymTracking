from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
import json
from datetime import date

from .models import WorkoutSession, SessionExercise, ExerciseSet, PersonalRecord
from .forms import WorkoutSessionForm, SessionExerciseForm, ExerciseSetForm
from exercises.models import Exercise


class SessionListView(LoginRequiredMixin, ListView):
    model = WorkoutSession
    template_name = 'sessions/list.html'
    context_object_name = 'sessions'
    paginate_by = 10

    def get_queryset(self):
        return WorkoutSession.objects.filter(
            user=self.request.user
        ).select_related('plan').prefetch_related('session_exercises')


class SessionDetailView(LoginRequiredMixin, DetailView):
    model = WorkoutSession
    template_name = 'sessions/detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        session_exercises = session.session_exercises.select_related('exercise').prefetch_related('sets').all()
        context['session_exercises'] = session_exercises
        context['add_exercise_form'] = SessionExerciseForm()
        context['set_form'] = ExerciseSetForm()
        return context


class SessionCreateView(LoginRequiredMixin, CreateView):
    model = WorkoutSession
    form_class = WorkoutSessionForm
    template_name = 'sessions/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        messages.success(self.request, 'Sesión creada correctamente.')
        return redirect('sessions:log', pk=self.object.pk)

    def get_initial(self):
        from datetime import datetime
        initial = super().get_initial()
        initial['date'] = date.today()
        initial['start_time'] = datetime.now().strftime('%H:%M')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nueva Sesión'
        context['submit_text'] = 'Crear Sesión'
        return context


class SessionUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkoutSession
    form_class = WorkoutSessionForm
    template_name = 'sessions/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('sessions:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Sesión actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Sesión'
        context['submit_text'] = 'Guardar Cambios'
        return context


@login_required
def session_log_view(request, pk):
    """Mobile-optimized session logging view."""
    import json as _json
    session = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    session_exercises = session.session_exercises.select_related('exercise').prefetch_related('sets').all()

    # Get plan exercises for today if plan is linked
    plan_exercises = []
    if session.plan:
        today_dow = session.date.weekday()
        plan_exercises = session.plan.plan_exercises.filter(
            day_of_week=today_dow
        ).select_related('exercise')

    all_exercises = Exercise.objects.filter(is_public=True).order_by('name').values(
        'pk', 'name', 'exercise_type'
    )
    # Build exercise type lookup and pre-fill data from last session
    exercise_types = {}
    last_set_data = {}
    for ex in all_exercises:
        exercise_types[str(ex['pk'])] = ex['exercise_type']
        # Find last set for this exercise by this user
        last_set = ExerciseSet.objects.filter(
            session_exercise__exercise_id=ex['pk'],
            session_exercise__session__user=request.user,
            session_exercise__session__date__lt=session.date,
        ).order_by('-session_exercise__session__date', '-set_number').first()
        if last_set:
            last_set_data[str(ex['pk'])] = {
                'reps': last_set.reps,
                'weight': float(last_set.weight) if last_set.weight else None,
                'duration_seconds': last_set.duration_seconds,
                'distance_meters': float(last_set.distance_meters) if last_set.distance_meters else None,
            }

    context = {
        'session': session,
        'session_exercises': session_exercises,
        'plan_exercises': plan_exercises,
        'all_exercises': Exercise.objects.filter(is_public=True).order_by('name'),
        'add_exercise_form': SessionExerciseForm(),
        'exercise_types_json': _json.dumps(exercise_types),
        'last_set_data_json': _json.dumps(last_set_data),
    }
    return render(request, 'sessions/log.html', context)


@login_required
@require_POST
def add_exercise_to_session(request, session_pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    session = get_object_or_404(WorkoutSession, pk=session_pk, user=request.user)
    form = SessionExerciseForm(request.POST)
    if form.is_valid():
        session_exercise = form.save(commit=False)
        session_exercise.session = session
        session_exercise.save()
        # Find last-set prefill data
        last_set = ExerciseSet.objects.filter(
            session_exercise__exercise=session_exercise.exercise,
            session_exercise__session__user=request.user,
            session_exercise__session__date__lt=session.date,
        ).order_by('-session_exercise__session__date', '-set_number').first()
        prefill = {}
        if last_set:
            prefill = {
                'reps': last_set.reps,
                'weight': float(last_set.weight) if last_set.weight is not None else None,
                'duration_seconds': last_set.duration_seconds,
                'distance_meters': float(last_set.distance_meters) if last_set.distance_meters is not None else None,
            }
        if is_ajax:
            return JsonResponse({
                'success': True,
                'id': session_exercise.pk,
                'exercise_name': session_exercise.exercise.name,
                'exercise_type': session_exercise.exercise.exercise_type,
                'prefill': prefill,
            })
        return redirect('sessions:log', pk=session_pk)
    else:
        if is_ajax:
            return JsonResponse({'success': False, 'errors': form.errors})
        return redirect('sessions:log', pk=session_pk)


@login_required
@require_POST
def log_set(request, session_exercise_pk):
    """AJAX endpoint to log individual sets quickly."""
    session_exercise = get_object_or_404(
        SessionExercise, pk=session_exercise_pk,
        session__user=request.user
    )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    set_number = data.get('set_number', session_exercise.sets.count() + 1)
    reps = data.get('reps')
    weight = data.get('weight')
    duration_seconds = data.get('duration_seconds')
    distance_meters = data.get('distance_meters')

    exercise_set = ExerciseSet.objects.create(
        session_exercise=session_exercise,
        set_number=int(set_number),
        reps=int(reps) if reps is not None else None,
        weight=float(weight) if weight is not None else None,
        duration_seconds=int(duration_seconds) if duration_seconds is not None else None,
        distance_meters=float(distance_meters) if distance_meters is not None else None,
        completed=True,
    )

    # Update sets_completed count
    session_exercise.sets_completed = session_exercise.sets.filter(completed=True).count()
    session_exercise.save()

    return JsonResponse({
        'success': True,
        'set_id': exercise_set.pk,
        'set_number': exercise_set.set_number,
        'reps': exercise_set.reps,
        'weight': str(exercise_set.weight) if exercise_set.weight is not None else None,
        'duration_seconds': exercise_set.duration_seconds,
        'distance_meters': str(exercise_set.distance_meters) if exercise_set.distance_meters is not None else None,
        'total_sets': session_exercise.sets_completed,
    })


@login_required
@require_POST
def delete_set(request, set_pk):
    """Delete a logged exercise set."""
    exercise_set = get_object_or_404(
        ExerciseSet, pk=set_pk,
        session_exercise__session__user=request.user
    )
    se = exercise_set.session_exercise
    exercise_set.delete()
    se.sets_completed = se.sets.filter(completed=True).count()
    se.save()
    return JsonResponse({'success': True, 'total_sets': se.sets_completed})


@login_required
@require_POST
def complete_session(request, pk):
    session = get_object_or_404(WorkoutSession, pk=pk, user=request.user)
    session.completed = True
    from datetime import datetime
    if not session.end_time:
        session.end_time = datetime.now().time()
    session.save()
    messages.success(request, '¡Sesión completada! ¡Buen trabajo!')
    return redirect('sessions:detail', pk=pk)


@login_required
def search_exercises(request):
    """AJAX endpoint to search and filter exercises."""
    query = request.GET.get('q', '').strip()
    muscle_group = request.GET.get('muscle_group', '').strip()
    exercise_type = request.GET.get('type', '').strip()

    exercises = Exercise.objects.filter(is_public=True)

    # Filter by search query
    if query:
        exercises = exercises.filter(
            models.Q(name__icontains=query) | models.Q(description__icontains=query)
        )

    # Filter by muscle group
    if muscle_group:
        exercises = exercises.filter(muscle_groups__name=muscle_group)

    # Filter by exercise type
    if exercise_type:
        exercises = exercises.filter(exercise_type=exercise_type)

    exercises = exercises.distinct().order_by('name').values(
        'pk', 'name', 'exercise_type', 'rest_time'
    )

    return JsonResponse({
        'success': True,
        'exercises': list(exercises)
    })


@login_required
@require_POST
def finish_exercise(request, session_pk, exercise_pk):
    """Mark an exercise as finished and move it to completed section."""
    session = get_object_or_404(WorkoutSession, pk=session_pk, user=request.user)
    session_exercise = get_object_or_404(
        SessionExercise,
        session=session,
        pk=exercise_pk
    )

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': 'Ejercicio finalizado',
            'exercise_id': session_exercise.pk
        })

    return redirect('sessions:log', pk=session_pk)

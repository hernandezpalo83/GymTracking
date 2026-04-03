import csv
import json
from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg, Max
from django.db.models.functions import TruncDate, TruncWeek
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView

from exercises.models import Exercise, MuscleGroup
from plans.models import TrainingPlan
from sessions.models import WorkoutSession, ExerciseSet, SessionExercise
from users.models import User

from .utils import (
    get_progress_data, get_exercise_data, get_all_exercises_data, get_type_data,
    get_muscle_data, get_consistency_data, get_performance_data
)
from .forms import (
    ProgressFilterForm, ExerciseFilterForm, TypeFilterForm,
    MuscleFilterForm, ConsistencyFilterForm, PerformanceFilterForm
)
from .pdf_generator import export_report_to_pdf


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _parse_date_filters(request, default_days=30):
    """Parse date_from / date_to GET params with quick range shortcuts.

    Returns (date_from, date_to) as date objects.
    """
    today = date.today()

    range_param = request.GET.get('range')
    if range_param == 'week':
        date_from = today - timedelta(days=today.weekday())
        date_to = today
    elif range_param == 'month':
        date_from = today.replace(day=1)
        date_to = today
    elif range_param == '30d':
        date_from = today - timedelta(days=30)
        date_to = today
    elif range_param == '90d':
        date_from = today - timedelta(days=90)
        date_to = today
    else:
        raw_from = request.GET.get('date_from')
        raw_to = request.GET.get('date_to')
        try:
            date_from = date.fromisoformat(raw_from) if raw_from else today - timedelta(days=default_days)
        except ValueError:
            date_from = today - timedelta(days=default_days)
        try:
            date_to = date.fromisoformat(raw_to) if raw_to else today
        except ValueError:
            date_to = today

    return date_from, date_to


def _resolve_target_user(request):
    """Resolve which user's data to query based on role and user_id param."""
    user = request.user
    user_id_param = request.GET.get('user_id')

    if user_id_param:
        if user.is_superuser:
            return get_object_or_404(User, pk=user_id_param)
        if user.is_supervisor:
            return get_object_or_404(User, pk=user_id_param, supervised_by=user)
    return user


def _get_accessible_users(request_user):
    """Return queryset of users accessible to request_user."""
    if request_user.is_superuser:
        return User.objects.all()
    if request_user.is_supervisor:
        return User.objects.filter(supervised_by=request_user)
    return User.objects.filter(pk=request_user.pk)


def _calculate_streak(user, as_of=None):
    """Consecutive day streak ending on as_of (defaults to today)."""
    if as_of is None:
        as_of = date.today()
    streak = 0
    check_date = as_of
    while True:
        has_session = WorkoutSession.objects.filter(
            user=user, date=check_date, completed=True
        ).exists()
        if has_session:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


# ---------------------------------------------------------------------------
# Existing views (unchanged)
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    user = request.user
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    sessions_this_week = WorkoutSession.objects.filter(
        user=user, date__gte=week_start
    ).count()

    sessions_this_month = WorkoutSession.objects.filter(
        user=user, date__gte=month_start
    ).count()

    total_sessions = WorkoutSession.objects.filter(user=user).count()

    active_plan = TrainingPlan.objects.filter(
        assigned_to=user, is_active=True
    ).first()

    recent_sessions = WorkoutSession.objects.filter(
        user=user
    ).select_related('plan').order_by('-date')[:5]

    streak = _calculate_streak(user)

    week_sessions = WorkoutSession.objects.filter(user=user, date__gte=week_start)
    volume_this_week = 0
    for session in week_sessions:
        volume_this_week += session.get_total_volume()

    athletes_data = []
    if user.is_supervisor:
        athletes = User.objects.filter(supervised_by=user)
        for athlete in athletes:
            athlete_sessions_week = WorkoutSession.objects.filter(
                user=athlete, date__gte=week_start
            ).count()
            athletes_data.append({
                'athlete': athlete,
                'sessions_this_week': athlete_sessions_week,
                'active_plan': TrainingPlan.objects.filter(assigned_to=athlete, is_active=True).first(),
            })

    weeks_data = []
    for i in range(7, -1, -1):
        week_s = today - timedelta(days=today.weekday() + 7 * i)
        week_e = week_s + timedelta(days=6)
        count = WorkoutSession.objects.filter(
            user=user, date__gte=week_s, date__lte=week_e
        ).count()
        weeks_data.append({
            'label': week_s.strftime('%d/%m'),
            'count': count,
        })

    context = {
        'sessions_this_week': sessions_this_week,
        'sessions_this_month': sessions_this_month,
        'total_sessions': total_sessions,
        'active_plan': active_plan,
        'recent_sessions': recent_sessions,
        'streak': streak,
        'volume_this_week': round(volume_this_week, 1),
        'athletes_data': athletes_data,
        'weeks_data': weeks_data,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def exercise_progress_view(request):
    user = request.user
    exercise_id = request.GET.get('exercise')
    exercise = None
    progress_data = []
    is_cardio = False

    # Resolve target user (supervisor/superuser can see others)
    target_user = _resolve_target_user(request)

    # Accessible users for dropdown
    accessible_users = _get_accessible_users(user)

    exercises = Exercise.objects.filter(is_public=True).order_by('name')

    # Date filters
    date_from, date_to = _parse_date_filters(request)

    if exercise_id:
        exercise = get_object_or_404(Exercise, pk=exercise_id)
        is_cardio = exercise.exercise_type == 'cardio'

        sets_qs = ExerciseSet.objects.filter(
            session_exercise__exercise=exercise,
            session_exercise__session__user=target_user,
            session_exercise__session__date__gte=date_from,
            session_exercise__session__date__lte=date_to,
            completed=True,
        ).select_related('session_exercise__session').order_by('session_exercise__session__date')

        date_maxweight = defaultdict(float)
        date_volume = defaultdict(float)

        for s in sets_qs:
            d = s.session_exercise.session.date.strftime('%d/%m/%Y')
            if is_cardio:
                metric = float(s.duration_seconds) if s.duration_seconds is not None else (
                    float(s.distance_meters) if s.distance_meters is not None else None
                )
                if metric is not None and metric > date_maxweight[d]:
                    date_maxweight[d] = metric
                if metric is not None:
                    date_volume[d] += metric
            else:
                if s.weight is not None:
                    w = float(s.weight)
                    if w > date_maxweight[d]:
                        date_maxweight[d] = w
                    if s.reps is not None:
                        date_volume[d] += w * s.reps

        for d in sorted(date_maxweight.keys()):
            progress_data.append({
                'date': d,
                'max_weight': date_maxweight[d],
                'volume': round(date_volume[d], 1),
            })

    # CSV export
    if request.GET.get('format') == 'csv' and exercise:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="progreso_{exercise.name}.csv"'
        writer = csv.writer(response)
        if is_cardio:
            writer.writerow(['Fecha', 'Tiempo/Distancia máx', 'Volumen total'])
        else:
            writer.writerow(['Fecha', 'Peso máximo (kg)', 'Volumen (kg)'])
        for row in progress_data:
            writer.writerow([row['date'], row['max_weight'], row['volume']])
        return response

    context = {
        'exercises': exercises,
        'selected_exercise': exercise,
        'progress_data': progress_data,
        'is_cardio': is_cardio,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'selected_user': target_user,
        'accessible_users': accessible_users,
        'can_filter_users': user.is_supervisor or user.is_superuser,
    }
    return render(request, 'reports/exercise_progress.html', context)


@login_required
def weekly_summary_view(request):
    user = request.user
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    sessions_this_week = WorkoutSession.objects.filter(
        user=user, date__gte=week_start
    ).select_related('plan').prefetch_related('session_exercises__sets')

    active_plan = TrainingPlan.objects.filter(assigned_to=user, is_active=True).first()
    planned_days = set()
    if active_plan:
        planned_days = set(
            active_plan.plan_exercises.values_list('day_of_week', flat=True).distinct()
        )

    days_data = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_sessions = [s for s in sessions_this_week if s.date == day_date]
        days_data.append({
            'date': day_date,
            'day_name': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][i],
            'sessions': day_sessions,
            'planned': i in planned_days,
            'completed': any(s.completed for s in day_sessions),
            'is_today': day_date == today,
            'is_future': day_date > today,
        })

    context = {
        'days_data': days_data,
        'week_start': week_start,
        'active_plan': active_plan,
        'total_sessions': len([d for d in days_data if d['sessions']]),
        'planned_days': len(planned_days),
    }
    return render(request, 'reports/weekly_summary.html', context)


@login_required
def progress_data_api(request):
    """JSON endpoint for chart data."""
    user = request.user
    exercise_id = request.GET.get('exercise_id')
    target_user_id = request.GET.get('user_id')

    if target_user_id and request.user.is_supervisor:
        target_user = get_object_or_404(User, pk=target_user_id, supervised_by=user)
    else:
        target_user = user

    if not exercise_id:
        return JsonResponse({'error': 'exercise_id required'}, status=400)

    exercise = get_object_or_404(Exercise, pk=exercise_id)

    sets = ExerciseSet.objects.filter(
        session_exercise__exercise=exercise,
        session_exercise__session__user=target_user,
        completed=True
    ).select_related('session_exercise__session').order_by('session_exercise__session__date')

    date_maxweight = defaultdict(float)
    date_volume = defaultdict(float)

    for s in sets:
        d = s.session_exercise.session.date.isoformat()
        if s.weight is not None:
            w = float(s.weight)
            if w > date_maxweight[d]:
                date_maxweight[d] = w
            if s.reps is not None:
                date_volume[d] += w * s.reps

    dates = sorted(date_maxweight.keys())

    return JsonResponse({
        'exercise': exercise.name,
        'labels': [d for d in dates],
        'max_weight': [date_maxweight[d] for d in dates],
        'volume': [round(date_volume[d], 1) for d in dates],
    })


# ---------------------------------------------------------------------------
# New reports
# ---------------------------------------------------------------------------

@login_required
def sessions_report_view(request):
    user = request.user
    today = date.today()

    date_from, date_to = _parse_date_filters(request)

    # Resolve target user
    target_user = _resolve_target_user(request)

    plan_id = request.GET.get('plan_id')

    sessions_qs = WorkoutSession.objects.filter(
        user=target_user,
        date__gte=date_from,
        date__lte=date_to,
    ).select_related('plan').prefetch_related('session_exercises__sets').order_by('-date')

    if plan_id:
        sessions_qs = sessions_qs.filter(plan_id=plan_id)

    # Build session rows
    session_rows = []
    for session in sessions_qs:
        exercise_count = session.session_exercises.count()
        volume = session.get_total_volume()
        duration = session.get_duration_minutes()
        session_rows.append({
            'id': session.pk,
            'date': session.date.strftime('%d/%m/%Y'),
            'date_iso': session.date.isoformat(),
            'duration': duration,
            'exercise_count': exercise_count,
            'volume': round(volume, 1),
            'plan_name': session.plan.name if session.plan else '—',
            'mood_emoji': session.get_mood_emoji(),
            'completed': session.completed,
        })

    # Summary stats
    total_sessions = len(session_rows)

    # Average per week
    if date_from and date_to:
        days_range = (date_to - date_from).days + 1
        weeks_range = max(days_range / 7, 1)
        avg_per_week = round(total_sessions / weeks_range, 1)
    else:
        avg_per_week = 0

    streak = _calculate_streak(target_user)

    # Chart data: sessions per day (for the period)
    day_counts = defaultdict(int)
    for row in session_rows:
        day_counts[row['date_iso']] += 1

    # Build a continuous range of dates for the chart
    chart_labels = []
    chart_counts = []
    current = date_from
    while current <= date_to:
        chart_labels.append(current.strftime('%d/%m'))
        chart_counts.append(day_counts.get(current.isoformat(), 0))
        current += timedelta(days=1)

    # Plans dropdown for filter
    accessible_users = _get_accessible_users(user)
    plans_qs = TrainingPlan.objects.filter(assigned_to=target_user).order_by('name')

    # CSV export
    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="sesiones.csv"'
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Duración (min)', 'Ejercicios', 'Volumen (kg)', 'Plan', 'Estado ánimo', 'Completada'])
        for row in session_rows:
            writer.writerow([
                row['date'], row['duration'] or '', row['exercise_count'],
                row['volume'], row['plan_name'], row['mood_emoji'],
                'Sí' if row['completed'] else 'No',
            ])
        return response

    context = {
        'session_rows': session_rows,
        'total_sessions': total_sessions,
        'avg_per_week': avg_per_week,
        'streak': streak,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'chart_labels': json.dumps(chart_labels),
        'chart_counts': json.dumps(chart_counts),
        'plans': plans_qs,
        'selected_plan_id': plan_id,
        'target_user': target_user,
        'accessible_users': accessible_users,
        'can_filter_users': user.is_supervisor or user.is_superuser,
        'selected_user_id': request.GET.get('user_id', ''),
        'active_range': request.GET.get('range', ''),
    }
    return render(request, 'reports/sessions_report.html', context)


@login_required
def plan_compliance_view(request):
    user = request.user

    date_from, date_to = _parse_date_filters(request)

    plan_id = request.GET.get('plan_id')

    # Plans accessible to this user
    plans_qs = TrainingPlan.objects.filter(assigned_to=user).order_by('name')

    plan = None
    compliance_rows = []
    days_trained = 0
    planned_sessions_count = 0
    calendar_weeks = []

    if plan_id:
        plan = get_object_or_404(TrainingPlan, pk=plan_id, assigned_to=user)

        # Planned days of week for this plan
        planned_days_of_week = set(
            plan.plan_exercises.values_list('day_of_week', flat=True).distinct()
        )

        # Sessions in period for this plan
        sessions_in_period = WorkoutSession.objects.filter(
            user=user,
            plan=plan,
            date__gte=date_from,
            date__lte=date_to,
        ).prefetch_related('session_exercises__sets').order_by('date')

        session_by_date = {s.date: s for s in sessions_in_period}
        days_trained = sessions_in_period.count()

        # Count planned sessions in the period
        current = date_from
        while current <= date_to:
            if current.weekday() in planned_days_of_week:
                planned_sessions_count += 1
            current += timedelta(days=1)

        # Compliance rows per session
        for session in sessions_in_period:
            exercises_done = session.session_exercises.count()
            volume = session.get_total_volume()
            # Get planned exercises for the day of week
            planned_exercises = plan.plan_exercises.filter(
                day_of_week=session.date.weekday()
            ).count()
            if planned_exercises > 0:
                pct = min(100, round(exercises_done / planned_exercises * 100))
            else:
                pct = 100 if exercises_done > 0 else 0

            compliance_rows.append({
                'date': session.date.strftime('%d/%m/%Y'),
                'exercises_done': exercises_done,
                'planned_exercises': planned_exercises,
                'pct': pct,
                'volume': round(volume, 1),
                'completed': session.completed,
            })

        # 7-day calendar grid: build weeks covering date_from to date_to
        # Start from Monday of the week containing date_from
        cal_start = date_from - timedelta(days=date_from.weekday())
        cal_end = date_to + timedelta(days=6 - date_to.weekday())
        DAY_NAMES = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        week = []
        current = cal_start
        while current <= cal_end:
            if current.weekday() == 0 and week:
                calendar_weeks.append(week)
                week = []
            is_planned = current.weekday() in planned_days_of_week
            is_trained = current in session_by_date
            is_in_range = date_from <= current <= date_to
            is_today = current == date.today()
            if is_in_range:
                if is_trained:
                    state = 'trained'
                elif is_planned and current < date.today():
                    state = 'missed'
                elif is_planned:
                    state = 'planned'
                else:
                    state = 'rest'
            else:
                state = 'out'
            week.append({
                'date': current,
                'day_label': DAY_NAMES[current.weekday()],
                'state': state,
                'is_today': is_today,
            })
            current += timedelta(days=1)
        if week:
            calendar_weeks.append(week)

    compliance_pct = 0
    if planned_sessions_count > 0:
        compliance_pct = min(100, round(days_trained / planned_sessions_count * 100))

    # CSV export
    if request.GET.get('format') == 'csv' and plan:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="cumplimiento_{plan.name}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Ejercicios realizados', 'Ejercicios planificados', '% Cumplimiento', 'Volumen (kg)', 'Completada'])
        for row in compliance_rows:
            writer.writerow([row['date'], row['exercises_done'], row['planned_exercises'], row['pct'], row['volume'], 'Sí' if row['completed'] else 'No'])
        return response

    context = {
        'plans': plans_qs,
        'plan': plan,
        'compliance_rows': compliance_rows,
        'days_trained': days_trained,
        'planned_sessions_count': planned_sessions_count,
        'compliance_pct': compliance_pct,
        'calendar_weeks': calendar_weeks,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'selected_plan_id': plan_id,
        'active_range': request.GET.get('range', ''),
    }
    return render(request, 'reports/plan_compliance.html', context)


@login_required
def muscle_groups_view(request):
    user = request.user

    date_from, date_to = _parse_date_filters(request)
    target_user = _resolve_target_user(request)
    accessible_users = _get_accessible_users(user)

    # Get session exercises in range for target user
    session_exercises = SessionExercise.objects.filter(
        session__user=target_user,
        session__date__gte=date_from,
        session__date__lte=date_to,
    ).select_related('exercise').prefetch_related('exercise__muscle_groups', 'sets')

    # Aggregate by muscle group
    mg_sessions = defaultdict(set)   # muscle_group_name -> set of session_ids
    mg_volume = defaultdict(float)   # muscle_group_name -> total volume

    for se in session_exercises:
        for mg in se.exercise.muscle_groups.all():
            mg_name = mg.get_name_display()
            mg_sessions[mg_name].add(se.session_id)
            for s in se.sets.all():
                if s.weight is not None and s.reps is not None:
                    mg_volume[mg_name] += float(s.weight) * s.reps

    # Build sorted rows
    mg_rows = []
    for mg_name in mg_volume:
        mg_rows.append({
            'name': mg_name,
            'session_count': len(mg_sessions[mg_name]),
            'volume': round(mg_volume[mg_name], 1),
        })
    mg_rows.sort(key=lambda r: r['volume'], reverse=True)

    chart_labels = json.dumps([r['name'] for r in mg_rows])
    chart_volumes = json.dumps([r['volume'] for r in mg_rows])
    chart_counts = json.dumps([r['session_count'] for r in mg_rows])

    # CSV export
    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="musculos.csv"'
        writer = csv.writer(response)
        writer.writerow(['Grupo muscular', 'Sesiones', 'Volumen (kg)'])
        for row in mg_rows:
            writer.writerow([row['name'], row['session_count'], row['volume']])
        return response

    context = {
        'mg_rows': mg_rows,
        'chart_labels': chart_labels,
        'chart_volumes': chart_volumes,
        'chart_counts': chart_counts,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'target_user': target_user,
        'accessible_users': accessible_users,
        'can_filter_users': user.is_supervisor or user.is_superuser,
        'selected_user_id': request.GET.get('user_id', ''),
        'active_range': request.GET.get('range', ''),
    }
    return render(request, 'reports/muscle_groups.html', context)


@login_required
def supervision_view(request):
    user = request.user

    # Only supervisors and superusers
    if not (user.is_supervisor or user.is_superuser):
        return redirect('reports:dashboard')

    date_from, date_to = _parse_date_filters(request)

    # Get athletes
    if user.is_superuser:
        athletes = User.objects.filter(role='athlete').order_by('first_name', 'last_name', 'username')
    else:
        athletes = User.objects.filter(supervised_by=user).order_by('first_name', 'last_name', 'username')

    athlete_rows = []
    for athlete in athletes:
        sessions_period = WorkoutSession.objects.filter(
            user=athlete,
            date__gte=date_from,
            date__lte=date_to,
        ).prefetch_related('session_exercises__sets')

        sessions_count = sessions_period.count()

        # Last session date
        last_session = WorkoutSession.objects.filter(user=athlete).order_by('-date').first()
        last_session_date = last_session.date if last_session else None

        # Active plan
        active_plan = TrainingPlan.objects.filter(assigned_to=athlete, is_active=True).first()

        # Total volume in period
        total_volume = 0.0
        for session in sessions_period:
            total_volume += session.get_total_volume()

        # Streak
        streak = _calculate_streak(athlete)

        athlete_rows.append({
            'athlete': athlete,
            'sessions_count': sessions_count,
            'last_session_date': last_session_date.strftime('%d/%m/%Y') if last_session_date else '—',
            'active_plan': active_plan,
            'total_volume': round(total_volume, 1),
            'streak': streak,
        })

    # Sort by sessions desc
    athlete_rows.sort(key=lambda r: r['sessions_count'], reverse=True)

    # CSV export
    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="supervision.csv"'
        writer = csv.writer(response)
        writer.writerow(['Atleta', 'Sesiones en el período', 'Última sesión', 'Plan activo', 'Volumen (kg)', 'Racha (días)'])
        for row in athlete_rows:
            writer.writerow([
                str(row['athlete']),
                row['sessions_count'],
                row['last_session_date'],
                row['active_plan'].name if row['active_plan'] else '—',
                row['total_volume'],
                row['streak'],
            ])
        return response

    context = {
        'athlete_rows': athlete_rows,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'active_range': request.GET.get('range', ''),
    }
    return render(request, 'reports/supervision.html', context)


@login_required
def user_activity_view(request):
    """Report: all exercises done by a user in a period, grouped by session."""
    user = request.user
    date_from, date_to = _parse_date_filters(request, default_days=30)
    target_user = _resolve_target_user(request)
    accessible_users = _get_accessible_users(user)

    sessions_qs = WorkoutSession.objects.filter(
        user=target_user,
        date__gte=date_from,
        date__lte=date_to,
    ).select_related('plan').prefetch_related(
        'session_exercises__exercise__muscle_groups',
        'session_exercises__sets',
    ).order_by('-date')

    session_blocks = []
    total_sets = 0
    total_volume = 0.0

    for session in sessions_qs:
        exercise_rows = []
        for se in session.session_exercises.all():
            is_cardio = se.exercise.exercise_type == 'cardio'
            sets_data = []
            se_volume = 0.0
            for s in se.sets.all():
                if is_cardio:
                    sets_data.append({
                        'set_number': s.set_number,
                        'duration_display': s.get_duration_display(),
                        'distance_meters': float(s.distance_meters) if s.distance_meters else None,
                        'pace_display': s.get_pace_display(),
                    })
                else:
                    vol = s.get_volume()
                    if vol:
                        se_volume += vol
                    sets_data.append({
                        'set_number': s.set_number,
                        'reps': s.reps,
                        'weight': float(s.weight) if s.weight else None,
                        'volume': round(vol, 1) if vol else None,
                    })
                total_sets += 1
            total_volume += se_volume
            exercise_rows.append({
                'exercise': se.exercise,
                'is_cardio': is_cardio,
                'sets': sets_data,
                'sets_count': len(sets_data),
                'volume': round(se_volume, 1) if not is_cardio else None,
            })
        session_blocks.append({
            'session': session,
            'exercise_rows': exercise_rows,
            'volume': round(sum(
                (r['volume'] or 0) for r in exercise_rows
            ), 1),
        })

    # CSV export
    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        fn = f"actividad_{target_user.username}.csv"
        response['Content-Disposition'] = f'attachment; filename="{fn}"'
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Ejercicio', 'Tipo', 'Serie', 'Reps', 'Peso (kg)', 'Volumen (kg)', 'Tiempo (s)', 'Distancia (m)', 'Ritmo'])
        for block in session_blocks:
            for row in block['exercise_rows']:
                for s in row['sets']:
                    if row['is_cardio']:
                        writer.writerow([
                            block['session'].date.strftime('%d/%m/%Y'),
                            row['exercise'].name, 'Cardio',
                            s['set_number'], '', '', '',
                            s.get('duration_display', ''),
                            s.get('distance_meters', ''),
                            s.get('pace_display', ''),
                        ])
                    else:
                        writer.writerow([
                            block['session'].date.strftime('%d/%m/%Y'),
                            row['exercise'].name, 'Fuerza',
                            s['set_number'],
                            s.get('reps', ''),
                            s.get('weight', ''),
                            s.get('volume', ''),
                            '', '', '',
                        ])
        return response

    range_shortcuts = [
        ('Esta semana', 'week'),
        ('Este mes', 'month'),
        ('30 días', '30d'),
        ('90 días', '90d'),
    ]
    context = {
        'session_blocks': session_blocks,
        'target_user': target_user,
        'accessible_users': accessible_users,
        'can_filter_users': user.is_supervisor or user.is_superuser,
        'selected_user_id': request.GET.get('user_id', ''),
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'active_range': request.GET.get('range', ''),
        'total_sessions': len(session_blocks),
        'total_sets': total_sets,
        'total_volume': round(total_volume, 1),
        'range_shortcuts': range_shortcuts,
    }
    return render(request, 'reports/user_activity.html', context)


# ==================== NUEVOS INFORMES (6 COMPLETOS) ====================

from .utils import (
    get_progress_data, get_exercise_data, get_type_data,
    get_muscle_data, get_consistency_data, get_performance_data
)
from .forms import (
    ProgressFilterForm, ExerciseFilterForm, TypeFilterForm,
    MuscleFilterForm, ConsistencyFilterForm, PerformanceFilterForm
)
from .pdf_generator import export_report_to_pdf


@login_required
def reports_list(request):
    """
    Lista de selección de informes disponibles
    """
    context = {
        'title': 'Mis Informes',
    }
    return render(request, 'reports/informe_list.html', context)


@login_required
def report_progress(request):
    """
    Informe: Progreso Personal
    """
    form = ProgressFilterForm(request.GET)
    period = request.GET.get('period', 'month')
    exercise_type = request.GET.get('exercise_type', '')

    data = get_progress_data(request.user, period, exercise_type or None)

    context = {
        'form': form,
        'data': data,
        'title': 'Mi Progreso',
        'report_type': 'progress',
    }
    return render(request, 'reports/informe_progress.html', context)


@login_required
def report_exercise(request):
    """
    Informe: Por Ejercicio
    """
    form = ExerciseFilterForm(request.GET)
    period = request.GET.get('period', 'month')
    exercise_type = request.GET.get('exercise_type', '')

    data = get_all_exercises_data(request.user, period, exercise_type or None)

    context = {
        'form': form,
        'data': data,
        'title': 'Por Ejercicio',
        'report_type': 'exercise',
    }
    return render(request, 'reports/informe_exercise.html', context)


@login_required
def report_type(request):
    """
    Informe: Por Tipo de Ejercicio
    """
    form = TypeFilterForm(request.GET)
    period = request.GET.get('period', 'month')

    data = get_type_data(request.user, period)

    context = {
        'form': form,
        'data': data,
        'title': 'Por Tipo de Ejercicio',
        'report_type': 'type',
    }
    return render(request, 'reports/informe_type.html', context)


@login_required
def report_muscle(request):
    """
    Informe: Por Grupo Muscular
    """
    form = MuscleFilterForm(request.GET)
    period = request.GET.get('period', 'month')
    muscle_group = request.GET.get('muscle_group', '')

    data = get_muscle_data(request.user, period, muscle_group or None)

    context = {
        'form': form,
        'data': data,
        'title': 'Por Grupo Muscular',
        'report_type': 'muscle',
    }
    return render(request, 'reports/informe_muscle.html', context)


@login_required
def report_consistency(request):
    """
    Informe: Consistencia
    """
    form = ConsistencyFilterForm(request.GET)
    weeks = int(request.GET.get('weeks', 4))

    data = get_consistency_data(request.user, weeks)

    context = {
        'form': form,
        'data': data,
        'title': 'Mi Consistencia',
        'report_type': 'consistency',
    }
    return render(request, 'reports/informe_consistency.html', context)


@login_required
def report_performance(request):
    """
    Informe: Rendimiento (Score)
    """
    form = PerformanceFilterForm(request.GET)
    period = request.GET.get('period', 'month')

    data = get_performance_data(request.user, period)

    context = {
        'form': form,
        'data': data,
        'title': 'Mi Rendimiento',
        'report_type': 'performance',
    }
    return render(request, 'reports/informe_performance.html', context)


@login_required
def export_report_pdf(request):
    """
    Exportar informe a PDF
    """
    report_type = request.POST.get('report_type', 'progress')
    period = request.POST.get('period', 'month')
    exercise_type = request.POST.get('exercise_type', '')
    exercise_id = request.POST.get('exercise_id')
    muscle_group = request.POST.get('muscle_group', '')
    weeks = int(request.POST.get('weeks', 4))

    kwargs = {
        'period': period,
        'exercise_type': exercise_type or None,
        'exercise_id': exercise_id,
        'muscle_group': muscle_group or None,
        'weeks': weeks,
    }

    pdf_buffer = export_report_to_pdf(request.user, report_type, **kwargs)

    if pdf_buffer:
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        filename = f"Informe_{report_type}_{date.today().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return redirect('reports:reports_list')

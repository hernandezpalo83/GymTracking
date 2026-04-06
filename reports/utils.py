"""
Utilidades para generación de reportes
Cálculos de volumen, calorías, progreso, etc.
"""

from datetime import datetime, timedelta, date
from django.db.models import Sum, Count, Avg, Max
from django.utils.timezone import now
from sessions.models import WorkoutSession, ExerciseSet, SessionExercise
from exercises.models import Exercise, MuscleGroup


# ==================== CÁLCULOS BASE ====================

def calculate_volume(session_exercises):
    """
    Calcula volumen total (kg) de un conjunto de ejercicios.
    Volumen = SUM(reps × weight)

    Args:
        session_exercises: QuerySet de SessionExercise

    Returns:
        float: Volumen total en kg
    """
    total = 0
    for se in session_exercises:
        for s in se.sets.filter(completed=True):
            if s.reps and s.weight:
                total += int(s.reps) * float(s.weight)
    return total


def calculate_session_volume(session):
    """
    Calcula volumen total de una sesión.

    Args:
        session: WorkoutSession object

    Returns:
        float: Volumen total
    """
    return calculate_volume(session.session_exercises.all())


def calculate_calories(session):
    """
    Calcula calorías quemadas en una sesión.

    Fórmula:
    - Fuerza: reps × weight × 0.00086
    - Cardio: MET × peso_usuario × (tiempo/3600)

    Args:
        session: WorkoutSession object

    Returns:
        float: Calorías estimadas
    """
    total = 0
    user_weight = float(session.user.weight_kg) if session.user.weight_kg else 70.0

    for se in session.session_exercises.all():
        ex = se.exercise
        for s in se.sets.filter(completed=True):
            if ex.exercise_type == 'strength':
                if s.reps and s.weight:
                    total += int(s.reps) * float(s.weight) * 0.00086
            elif ex.exercise_type == 'cardio':
                if s.duration_seconds:
                    total += ex.get_met() * user_weight * (s.duration_seconds / 3600)
            # flexibility no calcula calorías

    return round(total, 0)


def calculate_progress_percentage(current, previous):
    """
    Calcula porcentaje de progreso.

    Fórmula: (current - previous) / previous × 100%

    Args:
        current: Valor actual
        previous: Valor anterior

    Returns:
        float: Porcentaje de progreso
    """
    if previous == 0 or previous is None:
        return 0
    return round(((current - previous) / previous) * 100, 1)


def calculate_session_duration(session):
    """
    Calcula duración de una sesión en minutos.

    Args:
        session: WorkoutSession object

    Returns:
        int: Minutos
    """
    if session.start_time and session.end_time:
        from datetime import datetime as dt
        start = dt.combine(date.today(), session.start_time)
        end = dt.combine(date.today(), session.end_time)
        delta = end - start
        return int(delta.total_seconds() / 60)
    return 0


# ==================== FILTROS DE PERÍODO ====================

def get_sessions_by_period(user, period='month', custom_from=None, custom_to=None, completed_only=True):
    """
    Retorna sesiones filtradas por período.

    Args:
        user: Usuario
        period: 'week', 'month', '90d', 'year', 'custom'
        custom_from: Fecha inicio (si period='custom')
        custom_to: Fecha fin (si period='custom')
        completed_only: Solo sesiones completadas

    Returns:
        QuerySet: Sesiones filtradas
    """
    today = date.today()

    periods = {
        'week': today - timedelta(days=7),
        'month': today - timedelta(days=30),
        '90d': today - timedelta(days=90),
        'year': today - timedelta(days=365),
    }

    if period == 'custom' and custom_from and custom_to:
        start_date = custom_from
        end_date = custom_to
    else:
        start_date = periods.get(period, today - timedelta(days=30))
        end_date = today

    queryset = WorkoutSession.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('plan').prefetch_related('session_exercises__exercise__muscle_groups')

    if completed_only:
        queryset = queryset.filter(completed=True)

    return queryset.order_by('-date')


# ==================== DATOS PARA PROGRESO PERSONAL ====================

def get_progress_data(user, period='month', exercise_type=None):
    """
    Obtiene datos para el informe de Progreso Personal.

    Args:
        user: Usuario
        period: Período de tiempo
        exercise_type: Filtro por tipo (opcional)

    Returns:
        dict: Datos agregados
    """
    sessions = get_sessions_by_period(user, period)

    # Filtrar por tipo si es necesario
    if exercise_type:
        sessions_filtered = []
        for session in sessions:
            has_type = any(
                se.exercise.exercise_type == exercise_type
                for se in session.session_exercises.all()
            )
            if has_type:
                sessions_filtered.append(session)
        sessions = sessions_filtered

    # Calcular datos
    sessions_count = len(sessions)
    total_volume = sum(calculate_session_volume(s) for s in sessions)
    total_calories = sum(calculate_calories(s) for s in sessions)
    avg_duration = sum(calculate_session_duration(s) for s in sessions) / max(sessions_count, 1)

    # Progreso vs período anterior
    previous_period = get_sessions_by_period(user, period)  # Mismo período pero anterior
    previous_volume = sum(calculate_session_volume(s) for s in previous_period)
    progress = calculate_progress_percentage(total_volume, previous_volume)

    # Datos por fecha para gráfico
    volumes_by_date = {}
    for session in sessions:
        vol = calculate_session_volume(session)
        date_str = session.date.strftime('%Y-%m-%d')
        volumes_by_date[date_str] = vol

    return {
        'sessions_count': sessions_count,
        'total_volume': total_volume,
        'total_calories': int(total_calories),
        'avg_duration': int(avg_duration),
        'progress': progress,
        'sessions': sessions,
        'volumes_by_date': volumes_by_date,
        'dates': sorted(volumes_by_date.keys()),
        'volumes': [volumes_by_date[d] for d in sorted(volumes_by_date.keys())],
    }


# ==================== DATOS PARA EJERCICIO ====================

def get_exercise_data(user, exercise_id, limit=10):
    """
    Obtiene datos para el informe Por Ejercicio.

    Args:
        user: Usuario
        exercise_id: ID del ejercicio
        limit: Número de últimas sesiones

    Returns:
        dict: Datos del ejercicio
    """
    try:
        exercise = Exercise.objects.get(pk=exercise_id)
    except Exercise.DoesNotExist:
        return {}

    # Obtener todas las sesiones de este usuario con este ejercicio
    session_exercises = SessionExercise.objects.filter(
        exercise=exercise,
        session__user=user,
        session__completed=True
    ).select_related('session').prefetch_related('sets').order_by('-session__date')[:limit]

    # Datos del ejercicio
    sets_data = []
    for se in session_exercises:
        for s in se.sets.all():
            sets_data.append({
                'date': se.session.date,
                'set_number': s.set_number,
                'reps': s.reps,
                'weight': float(s.weight) if s.weight else None,
                'duration_seconds': s.duration_seconds,
                'distance_meters': float(s.distance_meters) if s.distance_meters else None,
            })

    if not sets_data:
        return {'sets_data': []}

    # PR (máximo peso)
    max_weight = max((s['weight'] for s in sets_data if s['weight']), default=0)
    max_reps = max((s['reps'] for s in sets_data if s['reps']), default=0)

    # Promedio últimas 3
    recent_weights = [s['weight'] for s in sets_data[:15] if s['weight']]
    avg_weight = sum(recent_weights) / len(recent_weights) if recent_weights else 0

    # Tendencia
    if len(recent_weights) >= 2:
        trend = "↑ Mejorando" if recent_weights[-1] > recent_weights[0] else \
                "↓ Bajando" if recent_weights[-1] < recent_weights[0] else \
                "→ Igual"
    else:
        trend = "→ Sin datos"

    # Frecuencia (veces en último mes)
    last_month = get_sessions_by_period(user, 'month')
    frequency = SessionExercise.objects.filter(
        exercise=exercise,
        session__in=last_month
    ).count()

    return {
        'exercise': exercise,
        'sets_data': sets_data[::-1],  # Invertir para mostrar más recientes primero
        'max_weight': max_weight,
        'max_reps': max_reps,
        'avg_weight': round(avg_weight, 1),
        'trend': trend,
        'frequency': frequency,
    }


def get_all_exercises_data(user, period='month', exercise_type=None):
    """
    Obtiene datos para todos los ejercicios en el informe Por Ejercicio.

    Args:
        user: Usuario
        period: Período de tiempo
        exercise_type: Filtro por tipo (opcional)

    Returns:
        dict: Datos de todos los ejercicios
    """
    sessions = get_sessions_by_period(user, period)

    # Filtrar por tipo si es necesario
    if exercise_type:
        sessions_filtered = []
        for session in sessions:
            has_type = any(
                se.exercise.exercise_type == exercise_type
                for se in session.session_exercises.all()
            )
            if has_type:
                sessions_filtered.append(session)
        sessions = sessions_filtered

    # Agregar datos por ejercicio
    exercises_data = {}
    top_exercises = {}

    for session in sessions:
        for se in session.session_exercises.all():
            ex_name = se.exercise.name
            ex_id = se.exercise.id

            if ex_name not in exercises_data:
                exercises_data[ex_name] = {
                    'name': ex_name,
                    'id': ex_id,
                    'set_count': 0,
                    'volume': 0,
                    'calories': 0,
                    'previous_volume': 0,
                }
                top_exercises[ex_name] = 0

            # Contar series
            set_count = se.sets.filter(completed=True).count()
            exercises_data[ex_name]['set_count'] += set_count

            # Calcular volumen y calorías
            vol = 0
            for s in se.sets.filter(completed=True):
                if s.reps and s.weight:
                    vol += int(s.reps) * float(s.weight)
            exercises_data[ex_name]['volume'] += vol
            top_exercises[ex_name] += vol

            # Calcular calorías
            if se.exercise.exercise_type == 'strength':
                for s in se.sets.filter(completed=True):
                    if s.reps and s.weight:
                        exercises_data[ex_name]['calories'] += int(s.reps) * float(s.weight) * 0.00086
            elif se.exercise.exercise_type == 'cardio':
                user_weight = float(user.weight_kg) if user.weight_kg else 70.0
                for s in se.sets.filter(completed=True):
                    if s.duration_seconds:
                        exercises_data[ex_name]['calories'] += se.exercise.get_met() * user_weight * (s.duration_seconds / 3600)

    # Calcular progreso para cada ejercicio
    previous_sessions = get_sessions_by_period(user, period,
                                               custom_from=date.today() - timedelta(days=60),
                                               custom_to=date.today() - timedelta(days=30))

    for ex_name in exercises_data:
        exercises_data[ex_name]['calories'] = int(exercises_data[ex_name]['calories'])
        exercises_data[ex_name]['volume'] = round(exercises_data[ex_name]['volume'], 1)

        # Buscar volumen anterior
        for session in previous_sessions:
            for se in session.session_exercises.all():
                if se.exercise.name == ex_name:
                    for s in se.sets.filter(completed=True):
                        if s.reps and s.weight:
                            exercises_data[ex_name]['previous_volume'] += int(s.reps) * float(s.weight)

        # Calcular progreso
        exercises_data[ex_name]['progress'] = calculate_progress_percentage(
            exercises_data[ex_name]['volume'],
            exercises_data[ex_name]['previous_volume']
        )

    # Top 5 ejercicios
    top_5 = sorted(top_exercises.items(), key=lambda x: x[1], reverse=True)[:5]
    top_exercises_names = [ex[0] for ex in top_5]
    top_exercises_volumes = [ex[1] for ex in top_5]

    return {
        'exercises': sorted(exercises_data.values(), key=lambda x: x['volume'], reverse=True),
        'top_exercises': top_5,
        'top_exercises_names': top_exercises_names,
        'top_exercises_volumes': top_exercises_volumes,
    }


# ==================== DATOS POR TIPO DE EJERCICIO ====================

def get_type_data(user, period='month', exercise_type=None):
    """
    Obtiene datos para el informe Por Tipo de Ejercicio.

    Args:
        user: Usuario
        period: Período
        exercise_type: Tipo específico o None (todos)

    Returns:
        dict: Datos por tipo
    """
    sessions = get_sessions_by_period(user, period)

    types = ['strength', 'cardio', 'flexibility']
    if exercise_type:
        types = [exercise_type]

    result = {}
    for ex_type in types:
        sessions_count = 0
        total_volume = 0
        total_calories = 0
        exercises_dict = {}

        for session in sessions:
            for se in session.session_exercises.all():
                if se.exercise.exercise_type == ex_type:
                    sessions_count += 1
                    vol = calculate_volume([se])
                    total_volume += vol
                    total_calories += calculate_calories(session)

                    # Top ejercicios
                    ex_name = se.exercise.name
                    if ex_name not in exercises_dict:
                        exercises_dict[ex_name] = 0
                    exercises_dict[ex_name] += vol

        # Ordenar ejercicios por volumen
        top_exercises = sorted(exercises_dict.items(), key=lambda x: x[1], reverse=True)[:5]

        result[ex_type] = {
            'type_display': dict(Exercise.TYPE_CHOICES).get(ex_type, ex_type),
            'sessions_count': sessions_count,
            'total_volume': total_volume,
            'total_calories': int(total_calories),
            'top_exercises': top_exercises,
            'percentage': 0,  # Se calcula después
        }

    # Calcular porcentajes
    total_sessions = sum(r['sessions_count'] for r in result.values())
    for ex_type in result:
        if total_sessions > 0:
            result[ex_type]['percentage'] = round(
                (result[ex_type]['sessions_count'] / total_sessions) * 100, 1
            )

    return result


# ==================== DATOS POR GRUPO MUSCULAR ====================

def get_muscle_data(user, period='month', muscle_group=None):
    """
    Obtiene datos para el informe Por Grupo Muscular.

    Args:
        user: Usuario
        period: Período
        muscle_group: Código del grupo o None (todos)

    Returns:
        dict: Datos por grupo muscular
    """
    sessions = get_sessions_by_period(user, period)

    # Obtener todos los grupos musculares
    all_groups = MuscleGroup.objects.all()
    if muscle_group:
        all_groups = all_groups.filter(name=muscle_group)

    result = {}
    for group in all_groups:
        sessions_count = 0
        total_volume = 0
        exercises_list = set()

        for session in sessions:
            for se in session.session_exercises.all():
                if group in se.exercise.muscle_groups.all():
                    sessions_count += 1
                    total_volume += calculate_volume([se])
                    exercises_list.add(se.exercise.name)

        result[group.name] = {
            'name': group.get_name_display(),
            'sessions_count': sessions_count,
            'total_volume': total_volume,
            'exercises': list(exercises_list)[:5],
            'frequency': sessions_count / 4 if sessions_count > 0 else 0,  # Por semana
        }

    return result


# ==================== DATOS CONSISTENCIA ====================

def get_consistency_data(user, weeks=4):
    """
    Obtiene datos para el informe de Consistencia.

    Args:
        user: Usuario
        weeks: Número de semanas a analizar

    Returns:
        dict: Datos de consistencia
    """
    today = date.today()

    # Racha actual
    current_streak = 0
    check_date = today
    while True:
        if WorkoutSession.objects.filter(user=user, date=check_date, completed=True).exists():
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Sesiones por semana (últimas N semanas)
    weeks_data = {}
    for i in range(weeks):
        week_start = today - timedelta(days=today.weekday() + i * 7)
        week_end = week_start + timedelta(days=7)

        sessions = WorkoutSession.objects.filter(
            user=user,
            date__gte=week_start,
            date__lt=week_end,
            completed=True
        ).count()

        week_key = week_start.strftime('%Y-W%U')
        weeks_data[week_key] = sessions

    # Calendario heatmap (últimas 4 semanas)
    heatmap_data = {}
    for i in range(28):
        check_date = today - timedelta(days=i)
        has_session = WorkoutSession.objects.filter(
            user=user,
            date=check_date,
            completed=True
        ).exists()
        heatmap_data[check_date.strftime('%Y-%m-%d')] = 1 if has_session else 0

    # Promedio sesiones/semana
    total_sessions = sum(weeks_data.values())
    avg_sessions_per_week = total_sessions / max(weeks, 1)

    return {
        'current_streak': current_streak,
        'avg_sessions_per_week': round(avg_sessions_per_week, 1),
        'weeks_data': weeks_data,
        'heatmap_data': heatmap_data,
        'total_sessions': total_sessions,
    }


# ==================== DATOS RENDIMIENTO ====================

def get_performance_data(user, period='month'):
    """
    Obtiene datos para el informe de Rendimiento (Score).

    Score = (Consistencia×0.3 + Volumen×0.3 + Calorías×0.2 + Progreso×0.2)

    Args:
        user: Usuario
        period: Período

    Returns:
        dict: Datos de rendimiento
    """
    # Datos base
    progress_data = get_progress_data(user, period)
    consistency_data = get_consistency_data(user)
    type_data = get_type_data(user, period)

    sessions_count = progress_data['sessions_count']
    total_volume = progress_data['total_volume']
    total_calories = progress_data['total_calories']
    progress = progress_data['progress']
    avg_sessions_per_week = consistency_data['avg_sessions_per_week']

    # Normalizar scores (0-100)
    consistency_score = min(100, (avg_sessions_per_week / 4) * 100)  # 4 sesiones/semana = 100
    volume_score = min(100, (total_volume / 10000) * 100)  # 10000 kg = 100
    calories_score = min(100, (total_calories / 5000) * 100)  # 5000 kcal = 100
    progress_score = max(0, min(100, 50 + progress))  # -50% = 0, +50% = 100

    # Score final
    overall_score = (
        consistency_score * 0.3 +
        volume_score * 0.3 +
        calories_score * 0.2 +
        progress_score * 0.2
    )

    # Top ejercicios
    all_exercises = {}
    for session in progress_data['sessions']:
        for se in session.session_exercises.all():
            ex_name = se.exercise.name
            if ex_name not in all_exercises:
                all_exercises[ex_name] = 0
            all_exercises[ex_name] += calculate_volume([se])

    top_exercises = sorted(all_exercises.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        'overall_score': round(overall_score, 0),
        'consistency_score': round(consistency_score, 0),
        'volume_score': round(volume_score, 0),
        'calories_score': round(calories_score, 0),
        'progress_score': round(progress_score, 0),
        'consistency': consistency_data['avg_sessions_per_week'],
        'total_volume': total_volume,
        'total_calories': total_calories,
        'progress': progress,
        'top_exercises': top_exercises,
        'sessions_count': sessions_count,
        'avg_duration': progress_data['avg_duration'],
    }

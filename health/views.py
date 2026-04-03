import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from sessions.models import WorkoutSession
from .models import HealthConnection, DailySteps, HealthSyncLog
from . import google_fit


@login_required
def connect_page(request):
    """Health integrations overview: shows connection status and sync history."""
    connection = None
    try:
        connection = request.user.health_connection
    except HealthConnection.DoesNotExist:
        pass

    today_steps = None
    if connection:
        try:
            ds = DailySteps.objects.get(user=request.user, date=timezone.now().date())
            today_steps = ds.steps
        except DailySteps.DoesNotExist:
            pass

    recent_logs = HealthSyncLog.objects.filter(user=request.user).order_by('-created_at')[:10]

    context = {
        'connection': connection,
        'today_steps': today_steps,
        'recent_logs': recent_logs,
        # Show the "Connect Google Fit" button only if credentials are configured
        'google_fit_configured': bool(
            getattr(settings, 'GOOGLE_FIT_CLIENT_ID', '')
        ),
    }
    return render(request, 'health/connect.html', context)


@login_required
def connect_google_fit(request):
    """Initiate Google Fit OAuth2 flow by redirecting to Google's consent screen."""
    if not getattr(settings, 'GOOGLE_FIT_CLIENT_ID', ''):
        messages.error(
            request,
            'Google Fit no está configurado en el servidor. '
            'Contacta al administrador para activar la integración.'
        )
        return redirect('health:connect')

    # Store a random state token in the session to prevent CSRF
    state = secrets.token_urlsafe(32)
    request.session['google_fit_oauth_state'] = state
    auth_url = google_fit.get_auth_url(state)
    return redirect(auth_url)


@login_required
def google_fit_callback(request):
    """Handle the OAuth2 callback from Google and store the tokens."""
    error = request.GET.get('error')
    if error:
        messages.error(request, f'Error al conectar Google Fit: {error}')
        return redirect('health:connect')

    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.pop('google_fit_oauth_state', None)

    if not code or state != saved_state:
        messages.error(request, 'La solicitud de autorización no es válida. Inténtalo de nuevo.')
        return redirect('health:connect')

    try:
        token_data = google_fit.exchange_code(code)
    except Exception as exc:
        messages.error(request, f'Error al obtener tokens de Google: {exc}')
        return redirect('health:connect')

    expires_in = token_data.get('expires_in', 3600)
    expiry = timezone.now() + timedelta(seconds=expires_in)

    HealthConnection.objects.update_or_create(
        user=request.user,
        defaults={
            'provider': 'google_fit',
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token', ''),
            'token_expiry': expiry,
        },
    )
    messages.success(request, '¡Google Fit conectado correctamente! Tus entrenamientos se sincronizarán automáticamente.')
    return redirect('health:connect')


@login_required
@require_POST
def disconnect(request):
    """Remove the user's health service connection."""
    try:
        request.user.health_connection.delete()
        messages.success(request, 'Cuenta de salud desconectada.')
    except HealthConnection.DoesNotExist:
        pass
    return redirect('health:connect')


@login_required
@require_POST
def sync_session(request, session_pk):
    """Manually sync a workout session to Google Fit. Returns JSON."""
    session = get_object_or_404(WorkoutSession, pk=session_pk, user=request.user)

    try:
        connection = request.user.health_connection
    except HealthConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No hay cuenta de salud conectada.'})

    try:
        result = google_fit.write_workout(connection, session)
        HealthSyncLog.objects.create(
            user=request.user,
            session=session,
            provider='google_fit',
            sync_type='workout',
            status='success' if not result.get('skipped') else 'skipped',
            data=result,
        )
        return JsonResponse({'success': True, 'data': result})
    except Exception as exc:
        HealthSyncLog.objects.create(
            user=request.user,
            session=session,
            provider='google_fit',
            sync_type='workout',
            status='error',
            error_message=str(exc),
        )
        return JsonResponse({'success': False, 'error': str(exc)})


@login_required
def refresh_steps(request):
    """Fetch today's step count from Google Fit, cache it, and return JSON.

    Called via AJAX from the dashboard when the user is connected to Google Fit.
    """
    try:
        connection = request.user.health_connection
    except HealthConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No conectado'})

    try:
        steps = google_fit.get_today_steps(connection)
        DailySteps.objects.update_or_create(
            user=request.user,
            date=timezone.now().date(),
            defaults={'steps': steps, 'source': 'google_fit'},
        )
        HealthSyncLog.objects.create(
            user=request.user,
            provider='google_fit',
            sync_type='steps_read',
            status='success',
            data={'steps': steps},
        )
        return JsonResponse({'success': True, 'steps': steps})
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)})

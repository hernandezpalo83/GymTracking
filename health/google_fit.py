"""Google Fit REST API client.

Handles OAuth2 token exchange, token refresh, writing workouts,
and reading daily step counts using only Python's standard library
(urllib) — no extra packages required.

Setup required:
  1. Create a project in Google Cloud Console.
  2. Enable the Fitness API.
  3. Create OAuth 2.0 Client ID credentials (Web application).
  4. Add the callback URL to Authorised redirect URIs.
  5. Set GOOGLE_FIT_CLIENT_ID, GOOGLE_FIT_CLIENT_SECRET, and
     GOOGLE_FIT_REDIRECT_URI in your .env file.
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

from django.conf import settings
from django.utils import timezone as django_tz

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_FIT_BASE = 'https://www.googleapis.com/fitness/v1/users/me'

# Scopes needed to write workouts and read step counts
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.write',
    'https://www.googleapis.com/auth/fitness.activity.read',
]


def get_auth_url(state: str) -> str:
    """Build the Google OAuth2 authorization URL."""
    params = {
        'client_id': settings.GOOGLE_FIT_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_FIT_REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',   # request refresh token
        'prompt': 'consent',        # always show consent screen so refresh token is returned
        'state': state,
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(code: str) -> dict:
    """Exchange an authorization code for access + refresh tokens."""
    data = urllib.parse.urlencode({
        'code': code,
        'client_id': settings.GOOGLE_FIT_CLIENT_ID,
        'client_secret': settings.GOOGLE_FIT_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_FIT_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }).encode()
    req = urllib.request.Request(GOOGLE_TOKEN_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def refresh_access_token(refresh_token: str) -> dict:
    """Refresh an expired access token using the stored refresh token."""
    data = urllib.parse.urlencode({
        'refresh_token': refresh_token,
        'client_id': settings.GOOGLE_FIT_CLIENT_ID,
        'client_secret': settings.GOOGLE_FIT_CLIENT_SECRET,
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request(GOOGLE_TOKEN_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _get_valid_token(connection) -> str:
    """Return a valid access token, refreshing it if expired."""
    if connection.is_token_expired() and connection.refresh_token:
        token_data = refresh_access_token(connection.refresh_token)
        connection.access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)
        connection.token_expiry = django_tz.now() + timedelta(seconds=expires_in)
        connection.save(update_fields=['access_token', 'token_expiry'])
    return connection.access_token


def _api_request(method: str, path: str, token: str, body: dict = None) -> dict:
    """Make an authenticated request to the Google Fitness API."""
    url = f"{GOOGLE_FIT_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def write_workout(connection, session) -> dict:
    """Write a completed workout session to Google Fit.

    Creates a Fitness session spanning the workout duration.
    Calories are written as a separate data point (best-effort).

    Returns a dict with sync details, or {'skipped': True} if times are missing.
    """
    token = _get_valid_token(connection)

    start_dt = _to_utc_datetime(session.date, session.start_time)
    end_dt = _to_utc_datetime(session.date, session.end_time)
    if start_dt is None or end_dt is None:
        return {'skipped': True, 'reason': 'missing start or end time'}

    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    start_ns = start_ms * 1_000_000
    end_ns = end_ms * 1_000_000
    calories = float(session.estimated_calories())
    duration_min = session.get_duration_minutes() or 0

    # Activity type 97 = strength training (Google Fit activity type code)
    activity_type = 97

    # 1. Create the Fitness session
    session_body = {
        'id': f'gymtracking-{session.pk}',
        'name': f'GymTracking – {session.date.isoformat()}',
        'description': session.notes or '',
        'startTimeMillis': str(start_ms),
        'endTimeMillis': str(end_ms),
        'activityType': activity_type,
        'application': {
            'detailsUrl': 'https://gymtracking.app',
            'name': 'GymTracking',
            'version': '1',
        },
    }
    _api_request('PUT', f'/sessions/gymtracking-{session.pk}', token, session_body)

    # 2. Write estimated calories (best-effort — don't fail the whole sync)
    if calories > 0:
        cal_source_id = (
            'derived:com.google.calories.expended:'
            'com.google.android.gms:merge_calories_expended'
        )
        cal_body = {
            'minStartTimeNs': str(start_ns),
            'maxEndTimeNs': str(end_ns),
            'dataSourceId': cal_source_id,
            'point': [{
                'startTimeNanos': str(start_ns),
                'endTimeNanos': str(end_ns),
                'dataTypeName': 'com.google.calories.expended',
                'value': [{'fpVal': calories}],
            }],
        }
        try:
            _api_request(
                'PATCH',
                f'/dataSources/{cal_source_id}/datasets/{start_ns}-{end_ns}',
                token,
                cal_body,
            )
        except Exception:
            pass

    return {
        'session_id': f'gymtracking-{session.pk}',
        'calories': calories,
        'duration_minutes': duration_min,
    }


def get_today_steps(connection) -> int:
    """Read today's total step count from Google Fit (aggregated from all sources)."""
    token = _get_valid_token(connection)

    from datetime import date as _date
    today = _date.today()
    # Start of today in UTC milliseconds
    start_ms = int(
        datetime(today.year, today.month, today.day, tzinfo=timezone.utc).timestamp() * 1000
    )
    end_ms = int(time.time() * 1000)

    body = {
        'aggregateBy': [{'dataTypeName': 'com.google.step_count.delta'}],
        'bucketByTime': {'durationMillis': str(end_ms - start_ms)},
        'startTimeMillis': str(start_ms),
        'endTimeMillis': str(end_ms),
    }
    result = _api_request('POST', '/dataset:aggregate', token, body)

    steps = 0
    for bucket in result.get('bucket', []):
        for dataset in bucket.get('dataset', []):
            for point in dataset.get('point', []):
                for val in point.get('value', []):
                    steps += val.get('intVal', 0)
    return steps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_utc_datetime(d, t):
    """Combine a date and time into a UTC-aware datetime. Returns None if t is None."""
    if t is None:
        return None
    return datetime.combine(d, t).replace(tzinfo=timezone.utc)

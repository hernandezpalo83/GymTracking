from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from datetime import date, timedelta
from django.http import JsonResponse

from .models import User
from .forms import RegisterForm, ProfileForm, AdminUserCreateForm, AdminUserEditForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('reports:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenido/a, {user.get_full_name() or user.username}!')
            return redirect('reports:dashboard')
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('reports:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or 'reports:dashboard'
            messages.success(request, f'Bienvenido/a, {user.get_full_name() or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('users:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})


@login_required
def dashboard_view(request):
    return redirect('reports:dashboard')


@login_required
def athletes_list_view(request):
    if not request.user.is_supervisor and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('reports:dashboard')

    if request.user.is_superuser:
        athletes = User.objects.filter(role=User.ROLE_ATHLETE)
    else:
        athletes = User.objects.filter(supervised_by=request.user)

    athletes = athletes.prefetch_related('sessions', 'training_plans')

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    athletes_data = []
    for athlete in athletes:
        sessions_this_week = athlete.sessions.filter(date__gte=week_start).count()
        total_sessions = athlete.sessions.count()
        active_plan = athlete.training_plans.filter(is_active=True).first()
        athletes_data.append({
            'athlete': athlete,
            'sessions_this_week': sessions_this_week,
            'total_sessions': total_sessions,
            'active_plan': active_plan,
        })

    context = {
        'athletes_data': athletes_data,
        'total_athletes': athletes.count(),
    }
    return render(request, 'users/athletes.html', context)


# ──────────────────────────────────────────────────────
#  SUPERUSER ADMIN PANEL
# ──────────────────────────────────────────────────────

def _superuser_required(view_func):
    """Decorator: requires request.user.is_superuser."""
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Solo los superusuarios pueden acceder a esta sección.')
            return redirect('reports:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


@_superuser_required
def admin_user_list(request):
    users = User.objects.all().order_by('username')
    context = {
        'users': users,
        'total': users.count(),
        'active': users.filter(is_active=True).count(),
        'supervisors': users.filter(role=User.ROLE_SUPERVISOR).count(),
        'athletes': users.filter(role=User.ROLE_ATHLETE).count(),
        'superusers': users.filter(is_superuser=True).count(),
    }
    return render(request, 'users/admin/user_list.html', context)


@_superuser_required
def admin_user_detail(request, pk):
    target = get_object_or_404(User, pk=pk)
    sessions_count = target.sessions.count()
    plans_count = target.training_plans.count()
    context = {
        'target': target,
        'sessions_count': sessions_count,
        'plans_count': plans_count,
    }
    return render(request, 'users/admin/user_detail.html', context)


@_superuser_required
def admin_user_create(request):
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario "{user.username}" creado correctamente.')
            return redirect('users:admin_user_list')
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = AdminUserCreateForm()

    return render(request, 'users/admin/user_form.html', {
        'form': form,
        'title': 'Crear Usuario',
        'submit_text': 'Crear Usuario',
    })


@_superuser_required
def admin_user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario "{target.username}" actualizado correctamente.')
            return redirect('users:admin_user_detail', pk=pk)
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = AdminUserEditForm(instance=target)

    return render(request, 'users/admin/user_form.html', {
        'form': form,
        'target': target,
        'title': f'Editar: {target.username}',
        'submit_text': 'Guardar Cambios',
    })


@_superuser_required
def admin_user_toggle_active(request, pk):
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        if target == request.user:
            messages.error(request, 'No puedes desactivar tu propia cuenta.')
        else:
            target.is_active = not target.is_active
            target.save()
            action = 'activado' if target.is_active else 'desactivado'
            messages.success(request, f'Usuario "{target.username}" {action} correctamente.')
    return redirect('users:admin_user_list')


@login_required
def toggle_dark_mode(request):
    """Toggle dark mode preference and save to user profile."""
    if request.method == 'POST':
        request.user.dark_mode = not request.user.dark_mode
        request.user.save(update_fields=['dark_mode'])
        return JsonResponse({'dark_mode': request.user.dark_mode})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import SiteSettings
from .forms import SiteSettingsForm


def _superuser_required(view_func):
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
def site_settings_view(request):
    settings_obj = SiteSettings.get()

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración guardada correctamente.')
            return redirect('config:settings')
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = SiteSettingsForm(instance=settings_obj)

    return render(request, 'config/settings.html', {'form': form, 'settings': settings_obj})

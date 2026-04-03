"""GymTracking URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reports.urls', namespace='reports')),
    path('users/', include('users.urls', namespace='users')),
    path('exercises/', include('exercises.urls', namespace='exercises')),
    path('plans/', include('plans.urls', namespace='plans')),
    path('sessions/', include('sessions.urls', namespace='sessions')),
    path('admin-config/', include('config.urls', namespace='config')),
    path('health/', include('health.urls', namespace='health')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

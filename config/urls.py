from django.urls import path
from . import views

app_name = 'config'

urlpatterns = [
    path('', views.site_settings_view, name='settings'),
]

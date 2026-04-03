from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('', views.connect_page, name='connect'),
    path('connect/google-fit/', views.connect_google_fit, name='connect_google_fit'),
    path('callback/', views.google_fit_callback, name='callback'),
    path('disconnect/', views.disconnect, name='disconnect'),
    path('sync/<int:session_pk>/', views.sync_session, name='sync_session'),
    path('steps/refresh/', views.refresh_steps, name='refresh_steps'),
]

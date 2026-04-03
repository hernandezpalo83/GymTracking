from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('exercise-progress/', views.exercise_progress_view, name='exercise_progress'),
    path('weekly-summary/', views.weekly_summary_view, name='weekly_summary'),
    path('api/progress/', views.progress_data_api, name='progress_data_api'),
    # New reports
    path('sesiones/', views.sessions_report_view, name='sessions_report'),
    path('cumplimiento/', views.plan_compliance_view, name='plan_compliance'),
    path('musculos/', views.muscle_groups_view, name='muscle_groups'),
    path('supervision/', views.supervision_view, name='supervision'),
    path('actividad/', views.user_activity_view, name='user_activity'),
    path('progreso/', views.progress_panel_view, name='progress_panel'),
]

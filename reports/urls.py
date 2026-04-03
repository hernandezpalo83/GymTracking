from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Informes originales (mantenidos)
    path('', views.dashboard_view, name='dashboard'),
    path('exercise-progress/', views.exercise_progress_view, name='exercise_progress'),
    path('weekly-summary/', views.weekly_summary_view, name='weekly_summary'),
    path('api/progress/', views.progress_data_api, name='progress_data_api'),
    path('sesiones/', views.sessions_report_view, name='sessions_report'),
    path('cumplimiento/', views.plan_compliance_view, name='plan_compliance'),
    path('musculos/', views.muscle_groups_view, name='muscle_groups'),
    path('supervision/', views.supervision_view, name='supervision'),
    path('actividad/', views.user_activity_view, name='user_activity'),

    # Nuevos 6 informes completos
    path('informes/', views.reports_list, name='reports_list'),
    path('informes/progreso/', views.report_progress, name='report_progress'),
    path('informes/ejercicio/', views.report_exercise, name='report_exercise'),
    path('informes/tipo/', views.report_type, name='report_type'),
    path('informes/musculo/', views.report_muscle, name='report_muscle'),
    path('informes/consistencia/', views.report_consistency, name='report_consistency'),
    path('informes/rendimiento/', views.report_performance, name='report_performance'),
    path('informes/export-pdf/', views.export_report_pdf, name='export_pdf'),
]

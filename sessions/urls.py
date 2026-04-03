from django.urls import path
from . import views

app_name = 'sessions'

urlpatterns = [
    path('', views.SessionListView.as_view(), name='list'),
    path('create/', views.SessionCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SessionDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.SessionUpdateView.as_view(), name='edit'),
    path('<int:pk>/log/', views.session_log_view, name='log'),
    path('<int:pk>/complete/', views.complete_session, name='complete'),
    path('<int:session_pk>/add-exercise/', views.add_exercise_to_session, name='add_exercise'),
    path('set/<int:session_exercise_pk>/log/', views.log_set, name='log_set'),
    path('set/<int:set_pk>/delete/', views.delete_set, name='delete_set'),
    path('exercises/search/', views.search_exercises, name='search_exercises'),
    path('<int:session_pk>/finish-exercise/<int:exercise_pk>/', views.finish_exercise, name='finish_exercise'),
    path('<int:pk>/repeat/', views.repeat_session, name='repeat'),
]

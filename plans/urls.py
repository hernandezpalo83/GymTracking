from django.urls import path
from . import views

app_name = 'plans'

urlpatterns = [
    path('', views.PlanListView.as_view(), name='list'),
    path('create/', views.PlanCreateView.as_view(), name='create'),
    path('<int:pk>/', views.PlanDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.PlanUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.PlanDeleteView.as_view(), name='delete'),
    path('<int:plan_pk>/add-exercise/', views.add_exercise_to_plan, name='add_exercise'),
    path('<int:plan_pk>/remove-exercise/<int:exercise_pk>/', views.remove_exercise_from_plan, name='remove_exercise'),
    path('<int:plan_pk>/repeat/', views.repeat_plan, name='repeat'),
]

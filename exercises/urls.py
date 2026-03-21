from django.urls import path
from . import views

app_name = 'exercises'

urlpatterns = [
    path('', views.ExerciseListView.as_view(), name='list'),
    path('create/', views.ExerciseCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ExerciseDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ExerciseUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ExerciseDeleteView.as_view(), name='delete'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('add/', views.StudentCreateView.as_view(), name='student_add'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('profile/', views.StudentSelfProfileView.as_view(), name='student_self_profile'),
    path('feedback/', views.FeedbackCreateView.as_view(), name='student_feedback_create'),
    path('feedback/analytics/', views.FeedbackAnalyticsView.as_view(), name='student_feedback_analytics'),
]

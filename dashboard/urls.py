from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home_view, name='dashboard_home'),
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('staff/', views.staff_dashboard_view, name='staff_dashboard'),
    path('student/', views.student_dashboard_view, name='student_dashboard'),
]

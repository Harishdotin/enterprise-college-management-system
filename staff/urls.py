from django.urls import path
from . import views

urlpatterns = [
    path('', views.StaffListView.as_view(), name='staff_list'),
    path('add/', views.StaffCreateView.as_view(), name='staff_add'),
    path('<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_edit'),
    path('<int:pk>/delete/', views.StaffDeleteView.as_view(), name='staff_delete'),
    path('profile/', views.StaffSelfProfileView.as_view(), name='staff_self_profile'),
]

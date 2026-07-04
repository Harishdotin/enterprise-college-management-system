from django.urls import path
from . import views

urlpatterns = [
    # Assignments
    path('', views.AssignmentListView.as_view(), name='assignment_list'),
    path('add/', views.AssignmentCreateView.as_view(), name='assignment_add'),
    path('<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('<int:pk>/edit/', views.AssignmentUpdateView.as_view(), name='assignment_edit'),
    path('<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment_delete'),
    path('<int:pk>/submit/', views.AssignmentSubmitView.as_view(), name='assignment_submit'),
    path('submission/<int:pk>/grade/', views.AssignmentGradeView.as_view(), name='assignment_grade'),
    
    # Study Materials
    path('materials/', views.StudyMaterialListView.as_view(), name='study_material_list'),
    path('materials/upload/', views.StudyMaterialUploadView.as_view(), name='study_material_upload'),
]

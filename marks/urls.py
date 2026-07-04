from django.urls import path
from . import views

urlpatterns = [
    # Exam CRUD
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exams/add/', views.ExamCreateView.as_view(), name='exam_add'),
    path('exams/<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('exams/<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
    
    # Status Controls
    path('exams/<int:pk>/publish/', views.ExamPublishView.as_view(), name='exam_publish'),
    path('exams/<int:pk>/publish-results/', views.PublishResultsView.as_view(), name='publish_results'),
    
    # Marks entries
    path('exams/<int:exam_id>/enter/', views.MarksEntryView.as_view(), name='marks_entry'),
    path('exams/<int:exam_id>/import/', views.MarksBulkUploadView.as_view(), name='marks_import'),
    path('exams/<int:exam_id>/export/', views.MarksExportView.as_view(), name='marks_export'),
    
    # Results & Hall Tickets
    path('results/', views.StudentResultsView.as_view(), name='student_results'),
    path('hallticket/', views.StudentHallTicketView.as_view(), name='student_hall_ticket'),
    
    # Performance Dashboard
    path('analytics/', views.AcademicPerformanceView.as_view(), name='academic_performance'),
]

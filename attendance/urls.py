from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.AttendanceDashboardView.as_view(), name='attendance_dashboard'),
    
    # Marking
    path('mark/', views.StudentAttendanceMarkView.as_view(), name='mark_attendance'),
    path('import/', views.StudentAttendanceImportView.as_view(), name='import_attendance'),
    path('export/', views.StudentAttendanceExportView.as_view(), name='export_attendance'),
    
    # Leaves
    path('leaves/', views.LeaveRequestListView.as_view(), name='leave_list'),
    path('leaves/apply/', views.LeaveRequestCreateView.as_view(), name='leave_apply'),
    path('leaves/<int:pk>/cancel/', views.LeaveRequestCancelView.as_view(), name='leave_cancel'),
    
    # Reviews queue
    path('reviews/', views.LeaveReviewListView.as_view(), name='leave_review_list'),
    path('reviews/<int:pk>/process/', views.LeaveReviewView.as_view(), name='leave_review_process'),
]

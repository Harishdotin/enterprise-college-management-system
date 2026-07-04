from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.FinancialDashboardView.as_view(), name='financial_dashboard'),
    
    # Billing Structures
    path('structures/', views.FeeStructureListView.as_view(), name='fee_structure_list'),
    path('structures/add/', views.FeeStructureCreateView.as_view(), name='fee_structure_add'),
    path('structures/<int:pk>/edit/', views.FeeStructureUpdateView.as_view(), name='fee_structure_edit'),
    path('structures/<int:pk>/delete/', views.FeeStructureDeleteView.as_view(), name='fee_structure_delete'),
    
    # Invoicing & Payments
    path('student/invoice/', views.StudentFeesListView.as_view(), name='student_fees_list'),
    path('student/invoice/<int:fee_id>/pay/', views.RecordPaymentView.as_view(), name='record_payment'),
    path('student/invoice/<int:fee_id>/fine/', views.FineManageView.as_view(), name='fine_manage'),
    
    # Receipts
    path('receipts/<int:pk>/', views.ReceiptDetailView.as_view(), name='receipt_detail'),
    
    # Reports
    path('reports/', views.FinancialReportsView.as_view(), name='financial_reports'),
    
    # Scholarships
    path('scholarships/', views.ScholarshipListView.as_view(), name='scholarship_list'),
    path('scholarships/add/', views.ScholarshipCreateView.as_view(), name='scholarship_add'),
]

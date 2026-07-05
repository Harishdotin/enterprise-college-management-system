from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Redirect base /ai/ to dedicated chat page /ai/chat/
    path('', lambda r: redirect('ai_assistant_dashboard'), name='ai_base_redirect'),

    path("db-check/", views.db_check),
    
    # Standalone AI Chat Page
    path('chat/', views.AIAssistantDashboardView.as_view(), name='ai_assistant_dashboard'),
    
    # AJAX / Fetch Endpoints
    path('chat/send/', views.AIChatSendView.as_view(), name='ai_chat_send'),
    path('chat/history/', views.AIChatHistoryView.as_view(), name='ai_chat_history'),
    path('chat/clear/', views.AIChatClearView.as_view(), name='ai_chat_clear'),
    
    # Document generation paths
    path('documents/', views.AIDocumentListView.as_view(), name='ai_document_list'),
    path('documents/create/', views.AIDocumentCreateView.as_view(), name='ai_document_create'),
    path('documents/<int:pk>/', views.AIDocumentPreviewView.as_view(), name='ai_document_preview'),
    path('documents/<int:pk>/regenerate/', views.AIDocumentRegenerateView.as_view(), name='ai_document_regenerate'),
    path('documents/<int:pk>/download/', views.AIDocumentDownloadView.as_view(), name='ai_document_download'),

    # Legacy predictions, search, analytics, config
    path('predictions/', views.AIPredictionsView.as_view(), name='ai_predictions'),
    path('search/', views.AISearchView.as_view(), name='ai_search'),
    path('analytics/', views.AIAnalyticsDashboardView.as_view(), name='ai_analytics'),
    path('config/', views.AIConfigView.as_view(), name='ai_config'),
]

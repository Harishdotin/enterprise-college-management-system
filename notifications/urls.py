from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('announcements/', views.AnnouncementBoardView.as_view(), name='announcements_board'),
    path('announcements/add/', views.AnnouncementCreateView.as_view(), name='announcement_add'),
    path('messages/', views.InboxView.as_view(), name='inbox'),
    path('messages/compose/', views.ComposeMessageView.as_view(), name='message_compose'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
]

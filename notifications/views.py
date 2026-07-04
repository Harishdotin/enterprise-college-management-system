from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone

from accounts.decorators import RoleRequiredMixin
from .models import Notification, Announcement, Message
from .forms import AnnouncementForm, DirectMessageForm

# ----------------- NOTIFICATION CENTER -----------------
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'user_notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('notification_list')


# ----------------- ANNOUNCEMENTS -----------------
class AnnouncementBoardView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'notifications/announcements.html'
    context_object_name = 'announcements'
    paginate_by = 10

    def get_queryset(self):
        now = timezone.now()
        qs = Announcement.objects.filter(
            publish_date__lte=now
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=now)
        )
        return qs.order_by('-publish_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AnnouncementForm()
        return context


class AnnouncementCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def post(self, request):
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, "Announcement posted successfully.")
        else:
            messages.error(request, "Invalid announcement parameters.")
        return redirect('announcements_board')


# ----------------- DIRECT MESSAGING / COMMUNICATION -----------------
class InboxView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'notifications/inbox.html'
    context_object_name = 'messages_list'
    paginate_by = 15

    def get_queryset(self):
        tab = self.request.GET.get('tab', 'inbox')
        if tab == 'sent':
            return Message.objects.filter(sender=self.request.user).select_related('recipient').order_by('-sent_at')
        return Message.objects.filter(recipient=self.request.user).select_related('sender').order_by('-sent_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab', 'inbox')
        context['compose_form'] = DirectMessageForm()
        return context


class ComposeMessageView(LoginRequiredMixin, View):
    def post(self, request):
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            
            # Notify recipient
            Notification.send_notification(
                user=msg.recipient,
                title="New Direct Message",
                message=f"You received a new message from {request.user.username}: '{msg.subject}'."
            )
            messages.success(request, f"Message sent to {msg.recipient.username}.")
        else:
            messages.error(request, "Failed to send message. Please check recipient details.")
        return redirect('inbox')


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'notifications/message_detail.html'
    context_object_name = 'message_obj'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Mark as read if user is recipient
        if obj.recipient == self.request.user and not obj.is_read:
            obj.is_read = True
            obj.save()
        return obj

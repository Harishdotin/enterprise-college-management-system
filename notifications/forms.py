from django import forms
from django.contrib.auth import get_user_model
from .models import Announcement, Message

User = get_user_model()

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'content', 'attachment', 'publish_date', 'expiry_date')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-input', 'style': 'padding-left:15px; width:100%;'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'publish_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class DirectMessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'})
    )

    class Meta:
        model = Message
        fields = ('recipient', 'subject', 'body')
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'body': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'style': 'padding-left:15px; width:100%;'}),
        }

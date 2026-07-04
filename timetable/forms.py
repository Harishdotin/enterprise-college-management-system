from django import forms
from .models import TimetableSlot

class TimetableSlotForm(forms.ModelForm):
    class Meta:
        model = TimetableSlot
        fields = '__all__'
        widgets = {
            'timetable_type': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'section': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'subject': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'faculty': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'classroom': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'placeholder': 'e.g. Room 102, Lab 3'}),
            'day': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

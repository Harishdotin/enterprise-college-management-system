import datetime
from django import forms
from django.core.exceptions import ValidationError
from .models import LeaveRequest

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ('leave_type', 'start_date', 'end_date', 'reason', 'supporting_document')
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
            'supporting_document': forms.ClearableFileInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean_start_date(self):
        start = self.cleaned_data.get('start_date')
        if start and start < datetime.date.today() - datetime.timedelta(days=7):
            raise ValidationError("You cannot apply for leave retrospectively past 7 days.")
        return start

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start > end:
            raise ValidationError("Leave end date must be on or after start date.")
        return cleaned_data


class LeaveReviewForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ('status', 'admin_comments')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'admin_comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
        }


class AttendanceImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Select Attendance CSV file",
        widget=forms.ClearableFileInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'})
    )

    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if file:
            if not file.name.endswith('.csv'):
                raise ValidationError("Only CSV files are supported.")
            if file.size > 2 * 1024 * 1024:
                raise ValidationError("CSV file must not exceed 2MB.")
        return file

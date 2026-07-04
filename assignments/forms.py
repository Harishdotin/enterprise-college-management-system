from django import forms
from django.core.exceptions import ValidationError
from .models import Assignment, AssignmentSubmission, StudyMaterial

ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.ppt', '.pptx', '.zip', '.png', '.jpg', '.jpeg', '.mp4']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file):
    if file:
        if file.size > MAX_FILE_SIZE:
            raise ValidationError("File size must not exceed 5MB.")
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(f"File extension '{ext}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    return file


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('title', 'description', 'file', 'department', 'course', 'semester', 'subject', 'due_date', 'maximum_marks')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'style': 'padding-left:15px; width:100%;'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'subject': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'maximum_marks': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean_file(self):
        return validate_file(self.cleaned_data.get('file'))


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ('file',)
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError("Please select a file to submit.")
        return validate_file(file)


class AssignmentGradeForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ('marks_obtained', 'faculty_comments')
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'step': '0.01'}),
            'faculty_comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width:100%;'}),
        }


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ('title', 'description', 'file', 'department', 'course', 'semester', 'subject')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width:100%;'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'subject': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError("Please upload a file.")
        return validate_file(file)

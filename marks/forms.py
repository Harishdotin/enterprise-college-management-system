from django import forms
from django.core.exceptions import ValidationError
from .models import GradeRule, Exam, StudentMark

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'exam_type': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'academic_year': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'section': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'subject': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'exam_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'maximum_marks': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'passing_marks': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        max_marks = cleaned_data.get('maximum_marks')
        pass_marks = cleaned_data.get('passing_marks')
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if max_marks and pass_marks and pass_marks > max_marks:
            raise ValidationError("Passing marks cannot exceed maximum exam marks.")
            
        if start and end and start >= end:
            raise ValidationError("End time must be after start time.")
            
        return cleaned_data


class GradeRuleForm(forms.ModelForm):
    class Meta:
        model = GradeRule
        fields = '__all__'
        widgets = {
            'grade_letter': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'min_score': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'grade_point': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'is_pass': forms.CheckboxInput(attrs={'class': 'checkbox-custom'}),
        }


class MarksEntryForm(forms.ModelForm):
    class Meta:
        model = StudentMark
        fields = ('student', 'marks_obtained', 'remarks')
        widgets = {
            'student': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'step': '0.01'}),
            'remarks': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class MarksBulkUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Select Marks CSV file",
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

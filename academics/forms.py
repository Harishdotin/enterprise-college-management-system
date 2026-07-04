from django import forms
from django.core.exceptions import ValidationError
from .models import Department, Course, Semester, Section, Subject, Class, FacultySubjectAssignment, AcademicYear

class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = '__all__'
        widgets = {
            'academic_year': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'placeholder': 'e.g. 2026-2027'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox-custom'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start >= end:
            raise ValidationError("Start date must be prior to end date.")
        return cleaned_data


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
            'hod': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'duration_years': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'total_semesters': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'
        widgets = {
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'number': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'academic_year': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start >= end:
            raise ValidationError("Start date must be prior to end date.")
        return cleaned_data


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'class_advisor': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = '__all__'
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'credits': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'faculty': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'subject_type': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = '__all__'
        widgets = {
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'section': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'class_advisor': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class FacultySubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = FacultySubjectAssignment
        fields = '__all__'
        widgets = {
            'faculty': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'subject': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'academic_year': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Student
from academics.models import Department, Course, Semester

class StudentForm(forms.ModelForm):
    """
    Form for Admins and Staff to create/update Student records.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all().order_by('name')
        self.fields['course'].queryset = Course.objects.all().order_by('name')
        self.fields['semester'].queryset = Semester.objects.all().order_by('course__code', 'number')

    class Meta:

        model = Student
        exclude = ('user', 'created_by')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'register_number': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'admission_number': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 2026-2027', 'style': 'padding-left:15px;'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'state': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'country': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'pin_code': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'section': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'gender': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'blood_group': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError("Enter a valid phone number (9-15 digits).")
        return phone

    def clean_parent_phone(self):
        phone = self.cleaned_data.get('parent_phone')
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError("Enter a valid parent phone number (9-15 digits).")
        return phone

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            if photo.size > 2 * 1024 * 1024:
                raise ValidationError("Profile image size must not exceed 2MB.")
            ext = photo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise ValidationError("Only JPG, JPEG, or PNG images are supported.")
        return photo


class StudentProfileForm(forms.ModelForm):
    """
    Form for Students to update their personal contact details.
    Restricts changes to administrative/academic keys.
    """
    class Meta:
        model = Student
        fields = (
            'full_name', 'email', 'phone_number', 'parent_name', 'parent_phone',
            'address', 'city', 'state', 'country', 'pin_code', 'profile_photo'
        )
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'state': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'country': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'pin_code': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError("Enter a valid phone number (9-15 digits).")
        return phone

    def clean_parent_phone(self):
        phone = self.cleaned_data.get('parent_phone')
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError("Enter a valid parent phone number (9-15 digits).")
        return phone

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            if photo.size > 2 * 1024 * 1024:
                raise ValidationError("Profile image size must not exceed 2MB.")
            ext = photo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise ValidationError("Only JPG, JPEG, or PNG images are supported.")
        return photo


from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('feedback_type', 'faculty', 'subject', 'rating', 'comments', 'is_anonymous')
        widgets = {
            'feedback_type': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'faculty': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'subject': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'rating': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'min': 1, 'max': 5}),
            'comments': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'checkbox-custom'}),
        }


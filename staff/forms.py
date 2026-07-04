import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Staff

class StaffForm(forms.ModelForm):
    """
    Form for Admins to register and update Staff members.
    """
    class Meta:
        model = Staff
        exclude = ('user', 'created_by')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'date_of_joining': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'qualification': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'designation': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'state': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'country': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'pin_code': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'gender': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'blood_group': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'employment_status': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError("Enter a valid phone number (9-15 digits).")
        return phone

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            if photo.size > 2 * 1024 * 1024:
                raise ValidationError("Profile photo size must not exceed 2MB.")
            ext = photo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise ValidationError("Only JPG, JPEG, or PNG images are supported.")
        return photo


class StaffProfileForm(forms.ModelForm):
    """
    Form for Staff members to self-update their contact details.
    """
    class Meta:
        model = Staff
        fields = (
            'full_name', 'email', 'phone_number', 'address', 'city', 
            'state', 'country', 'pin_code', 'profile_photo'
        )
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
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

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            if photo.size > 2 * 1024 * 1024:
                raise ValidationError("Profile photo size must not exceed 2MB.")
            ext = photo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise ValidationError("Only JPG, JPEG, or PNG images are supported.")
        return photo

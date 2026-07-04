from django import forms
from .models import AIConfiguration

class AIConfigForm(forms.ModelForm):
    class Meta:
        model = AIConfiguration
        fields = ('is_enabled', 'provider', 'api_key', 'model_name', 'temperature')
        widgets = {
            'is_enabled': forms.CheckboxInput(attrs={'class': 'checkbox-custom'}),
            'provider': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'api_key': forms.PasswordInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'placeholder': '••••••••••••••••'}),
            'model_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'step': '0.1', 'min': '0.0', 'max': '1.0'}),
        }

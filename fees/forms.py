from django import forms
from django.core.exceptions import ValidationError
from .models import FeeCategory, FeeStructure, Scholarship, StudentFee, Payment

class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input', 'style': 'padding-left:15px; width: 100%;'}),
        }


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'department': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'course': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'semester': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'academic_year': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'category': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class ScholarshipForm(forms.ModelForm):
    class Meta:
        model = Scholarship
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'min': 0, 'max': 100}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'eligible_students': forms.SelectMultiple(attrs={'class': 'form-input', 'style': 'padding-left:15px; height: 120px;'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox-custom'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pct = cleaned_data.get('percentage')
        amt = cleaned_data.get('amount')
        
        if pct and amt and pct > 0 and amt > 0:
            raise ValidationError("You must specify either a percentage discount OR an absolute amount discount, not both.")
        if (not pct or pct == 0) and (not amt or amt == 0):
            raise ValidationError("You must specify either a percentage discount or an absolute amount discount.")
        return cleaned_data


class RecordPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('amount_paid', 'payment_mode', 'transaction_id', 'remarks')
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'step': '0.01'}),
            'payment_mode': forms.Select(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;', 'placeholder': 'e.g. TXN982347'}),
            'remarks': forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'}),
        }


class FineAdjustmentForm(forms.Form):
    fine_amount = forms.DecimalField(
        max_digits=8, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'})
    )
    remarks = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-input', 'style': 'padding-left:15px;'})
    )

from django import forms
from welfare_app.models import Hospital, Doctor
from .employee_forms import TailwindMixin


class HospitalForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Hospital
        exclude = ['created_at', 'updated_at']
        widgets = {
            'contract_start_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class DoctorForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ['created_at']

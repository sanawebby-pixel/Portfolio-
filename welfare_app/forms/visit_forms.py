from django import forms
from welfare_app.models import HospitalVisit
from .employee_forms import TailwindMixin


class HospitalVisitForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = HospitalVisit
        exclude = ['created_at', 'updated_at']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'discharge_date': forms.DateInput(attrs={'type': 'date'}),
            'followup_date': forms.DateInput(attrs={'type': 'date'}),
            'symptoms': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'prescription': forms.Textarea(attrs={'rows': 3}),
            'lab_tests': forms.Textarea(attrs={'rows': 3}),
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
        }

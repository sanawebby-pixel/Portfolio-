from django import forms
from welfare_app.models import Department, BenefitRule
from .employee_forms import TailwindMixin


class DepartmentForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'is_active']
        labels = {
            'name': 'Department Name',
            'code': 'Department Code (e.g. ENG, HR, PROD)',
            'description': 'Description & Scope',
            'is_active': 'Active Status',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Engineering & Maintenance'}),
            'code': forms.TextInput(attrs={'placeholder': 'e.g. ENG-01'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional department description...'}),
        }


class BenefitRuleForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = BenefitRule
        fields = [
            'name', 'department', 'grade_scale',
            'annual_medical_limit', 'opd_consultation_limit',
            'lab_coverage_percent', 'medicine_coverage_percent',
            'room_per_day_limit', 'is_active', 'description'
        ]
        labels = {
            'name': 'Benefit Policy / Rule Title',
            'department': 'Applicable Department (Leave blank for All)',
            'grade_scale': 'Applicable Grade / Scale',
            'annual_medical_limit': 'Annual Medical Allowance Limit (Rs.)',
            'opd_consultation_limit': 'Per OPD Consultation Limit (Rs.)',
            'lab_coverage_percent': 'Laboratory Coverage Percentage (%)',
            'medicine_coverage_percent': 'Medicine Coverage Percentage (%)',
            'room_per_day_limit': 'Room / Bed Per Day Limit (Rs.)',
            'is_active': 'Rule Active Status',
            'description': 'Policy Details & Exception Rules',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Standard Factory Staff Medical Policy'}),
            'grade_scale': forms.TextInput(attrs={'placeholder': 'e.g. All Scales, Scale 1-15, Scale 16+'}),
            'annual_medical_limit': forms.NumberInput(attrs={'step': '1000', 'class': 'font-mono font-bold'}),
            'opd_consultation_limit': forms.NumberInput(attrs={'step': '100', 'class': 'font-mono'}),
            'lab_coverage_percent': forms.NumberInput(attrs={'step': '1', 'min': '0', 'max': '100', 'class': 'font-mono'}),
            'medicine_coverage_percent': forms.NumberInput(attrs={'step': '1', 'min': '0', 'max': '100', 'class': 'font-mono'}),
            'room_per_day_limit': forms.NumberInput(attrs={'step': '500', 'class': 'font-mono'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Coverage rules, pre-authorization requirements...'}),
        }

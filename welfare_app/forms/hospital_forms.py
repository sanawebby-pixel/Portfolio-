from django import forms
from welfare_app.models import Hospital, Doctor
from .employee_forms import TailwindMixin


class HospitalForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Hospital
        exclude = ['created_at', 'updated_at']
        labels = {
            'hospital_code': 'Hospital / Clinic Code',
            'name': 'Hospital / Clinic Name',
            'hospital_type': 'Facility Type',
            'address': 'Complete Address',
            'city': 'City / Location',
            'contact_person': 'Contact Person / Liaison Officer',
            'contact_number': 'Phone / UAN Number',
            'email': 'Official Email Address',
            'panel_status': 'Panel / Contract Status',
            'contract_start_date': 'Contract Start Date',
            'contract_end_date': 'Contract Expiry Date',
            'status': 'Operational Status',
            'notes': 'Special Terms & Notes',
        }
        widgets = {
            'hospital_code': forms.TextInput(attrs={'placeholder': 'e.g. HOSP-001 (Auto-assigned if blank)'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Al-Shifa Trust Hospital'}),
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Full street address & sector...'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Islamabad'}),
            'contact_person': forms.TextInput(attrs={'placeholder': 'e.g. Dr. Salman Qureshi'}),
            'contact_number': forms.TextInput(attrs={'placeholder': 'e.g. +92 51 5487821'}),
            'email': forms.EmailInput(attrs={'placeholder': 'e.g. billing@alshifa.org'}),
            'contract_start_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Panel discount agreements, special welfare rates...'}),
        }


class DoctorForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ['created_at']
        labels = {
            'name': 'Doctor Name',
            'specialization': 'Medical Specialization',
            'hospital': 'Affiliated Hospital / Clinic',
            'contact': 'Phone / Contact Number',
            'email': 'Email Address',
            'registration_number': 'PMC / PMDC Registration Number',
            'consultation_fee': 'Standard Consultation Fee (Rs.)',
            'status': 'Status',
            'notes': 'Doctor Profile Notes',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Dr. Tariq Mahmood Khan'}),
            'specialization': forms.TextInput(attrs={'placeholder': 'e.g. Senior Consultant Cardiologist'}),
            'contact': forms.TextInput(attrs={'placeholder': 'e.g. +92 301 5551234'}),
            'email': forms.EmailInput(attrs={'placeholder': 'e.g. dr.tariq@alshifa.org'}),
            'registration_number': forms.TextInput(attrs={'placeholder': 'e.g. PMC-45892-C'}),
            'consultation_fee': forms.NumberInput(attrs={'placeholder': 'e.g. 2500', 'min': '0'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'OPD timings, clinic schedule, etc.'}),
        }

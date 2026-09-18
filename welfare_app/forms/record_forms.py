from django import forms
from welfare_app.models import MedicalRecord

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'employee', 'treatment_date', 'hospital', 'doctor', 'diagnosis',
            'doctor_fee', 'lab_fee', 'medicine_fee', 'admission_fee', 'other_fee',
            'bill_no', 'status'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white focus:outline-none focus:border-blue-500'}),
            'treatment_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'hospital': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Shifa Hospital'}),
            'doctor': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Dr. Khan'}),
            'diagnosis': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Routine Checkup / Lab tests / Fever'}),
            'doctor_fee': forms.NumberInput(attrs={'class': 'exp-input w-full px-2 py-1.5 border rounded bg-white', 'min': '0', 'value': '0'}),
            'lab_fee': forms.NumberInput(attrs={'class': 'exp-input w-full px-2 py-1.5 border rounded bg-white', 'min': '0', 'value': '0'}),
            'medicine_fee': forms.NumberInput(attrs={'class': 'exp-input w-full px-2 py-1.5 border rounded bg-white', 'min': '0', 'value': '0'}),
            'admission_fee': forms.NumberInput(attrs={'class': 'exp-input w-full px-2 py-1.5 border rounded bg-white', 'min': '0', 'value': '0'}),
            'other_fee': forms.NumberInput(attrs={'class': 'exp-input w-full px-2 py-1.5 border rounded bg-white', 'min': '0', 'value': '0'}),
            'bill_no': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'BILL-9901'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
        }

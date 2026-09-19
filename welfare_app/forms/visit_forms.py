from django import forms
from welfare_app.models import HospitalVisit, Employee, Dependent, Hospital, Doctor
from .employee_forms import TailwindMixin


class HospitalVisitForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = HospitalVisit
        exclude = ['created_at', 'updated_at']
        labels = {
            'employee': 'Employee (Search / Select)',
            'dependent': 'Patient Dependent / Family Member (Optional)',
            'hospital': 'Hospital / Clinic',
            'doctor': 'Attending Doctor',
            'department_specialization': 'Medical Department / Unit',
            'visit_date': 'Consultation / Visit Date',
            'visit_type': 'Visit Type',
            'diagnosis': 'Clinical Diagnosis / Chief Complaint',
            'symptoms': 'Reported Symptoms',
            'treatment': 'Treatment & Clinical Procedures',
            'prescription': 'Prescribed Medications & Dosage',
            'lab_tests': 'Diagnostic / Lab Tests Advised',
            'total_visit_cost': 'Total Visit Cost / Charges (Rs.)',
            'attached_document': 'Attach Prescription / Discharge Slip / Bill',
            'admission_date': 'Admission Date (If Inpatient)',
            'discharge_date': 'Discharge Date (If Inpatient)',
            'room_ward': 'Room / Ward / Bed Number',
            'followup_date': 'Follow-up Date Advised',
            'status': 'Visit Status',
            'remarks': 'Doctor / Welfare Officer Remarks',
        }
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'discharge_date': forms.DateInput(attrs={'type': 'date'}),
            'followup_date': forms.DateInput(attrs={'type': 'date'}),
            'diagnosis': forms.TextInput(attrs={'placeholder': 'e.g. Acute Bronchitis & Respiratory Infection'}),
            'department_specialization': forms.TextInput(attrs={'placeholder': 'e.g. Pulmonology / General Medicine'}),
            'symptoms': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Persistent dry cough, fever for 3 days, breathing discomfort...'}),
            'treatment': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Nebulization, antibiotic therapy administered in OPD...'}),
            'prescription': forms.Textarea(attrs={'rows': 3, 'placeholder': '1. Tab Augmentin 625mg 1 tab BD x 5 days\n2. Syp Hydryllin 2 tsp TDS\n3. Tab Panadol Extra 1 tab TDS'}),
            'lab_tests': forms.Textarea(attrs={'rows': 2, 'placeholder': 'CBC, Chest X-Ray PA View...'}),
            'total_visit_cost': forms.NumberInput(attrs={'placeholder': 'e.g. 4500', 'min': '0'}),
            'room_ward': forms.TextInput(attrs={'placeholder': 'e.g. Executive Room 204'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Advised 3 days medical leave...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.all().order_by('name')
        self.fields['hospital'].queryset = Hospital.objects.filter(status='Active').order_by('name')
        self.fields['doctor'].queryset = Doctor.objects.filter(status='Active').order_by('name')
        if 'total_visit_cost' in self.fields:
            self.fields['total_visit_cost'].required = False
        if 'attached_document' in self.fields:
            self.fields['attached_document'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if 'total_visit_cost' in cleaned_data and cleaned_data['total_visit_cost'] in [None, '']:
            cleaned_data['total_visit_cost'] = 0.00
        return cleaned_data

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
            'doctor_fee': 'Consultation Fee / Doctor Fee (Rs.)',
            'doctor_fee_doc': 'Doctor Fee Slip / Consultation Receipt',
            'medicine_cost': 'Medicine Cost (Rs.)',
            'medicine_doc': 'Medicine Bill / Pharmacy Slip',
            'diagnostic_cost': 'Diagnostic & Lab Tests Cost (Rs.)',
            'diagnostic_doc': 'Diagnostic / Lab Bill & Report',
            'other_charges': 'Other Hospital Charges / Miscellaneous (Rs.)',
            'other_charges_doc': 'Other Charges Invoice / Receipt',
            'total_visit_cost': 'Total Visit Cost / Charges (Rs.) (Auto-calculated)',
            'attached_document': 'General Prescription / Discharge Slip / Document',
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
            'doctor_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '0.01', 'id': 'id_doctor_fee', 'class': 'fee-input'}),
            'doctor_fee_doc': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-cyan-400 hover:file:bg-slate-700 cursor-pointer'}),
            'medicine_cost': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '0.01', 'id': 'id_medicine_cost', 'class': 'fee-input'}),
            'medicine_doc': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-cyan-400 hover:file:bg-slate-700 cursor-pointer'}),
            'diagnostic_cost': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '0.01', 'id': 'id_diagnostic_cost', 'class': 'fee-input'}),
            'diagnostic_doc': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-cyan-400 hover:file:bg-slate-700 cursor-pointer'}),
            'other_charges': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '0.01', 'id': 'id_other_charges', 'class': 'fee-input'}),
            'other_charges_doc': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-cyan-400 hover:file:bg-slate-700 cursor-pointer'}),
            'total_visit_cost': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '0.01', 'id': 'id_total_visit_cost', 'class': 'font-mono font-bold text-emerald-400 bg-slate-900'}),
            'room_ward': forms.TextInput(attrs={'placeholder': 'e.g. Executive Room 204'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Advised 3 days medical leave...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.all().order_by('name')
        self.fields['hospital'].queryset = Hospital.objects.filter(status='Active').order_by('name')
        self.fields['doctor'].queryset = Doctor.objects.filter(status='Active').order_by('name')

        optional_fields = [
            'doctor_fee', 'doctor_fee_doc',
            'medicine_cost', 'medicine_doc',
            'diagnostic_cost', 'diagnostic_doc',
            'other_charges', 'other_charges_doc',
            'total_visit_cost', 'attached_document',
            'admission_date', 'discharge_date', 'room_ward',
            'followup_date', 'remarks', 'diagnosis',
            'symptoms', 'treatment', 'prescription', 'lab_tests',
            'department_specialization', 'dependent', 'hospital', 'doctor'
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()

        doc_fee = cleaned_data.get('doctor_fee') or 0.00
        med_cost = cleaned_data.get('medicine_cost') or 0.00
        diag_cost = cleaned_data.get('diagnostic_cost') or 0.00
        other_cost = cleaned_data.get('other_charges') or 0.00

        cleaned_data['doctor_fee'] = doc_fee
        cleaned_data['medicine_cost'] = med_cost
        cleaned_data['diagnostic_cost'] = diag_cost
        cleaned_data['other_charges'] = other_cost

        itemized_total = doc_fee + med_cost + diag_cost + other_cost
        entered_total = cleaned_data.get('total_visit_cost') or 0.00

        if itemized_total > 0:
            cleaned_data['total_visit_cost'] = itemized_total
        else:
            cleaned_data['total_visit_cost'] = entered_total

        return cleaned_data

from django import forms
from welfare_app.models import Employee, Dependent, Department


class TailwindMixin:
    """Mixin that auto-applies Tailwind CSS classes to all form fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': f'{current_classes} w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs sm:text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors shadow-sm'.strip()
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': f'{current_classes} w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs sm:text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors shadow-sm'.strip(),
                    'rows': field.widget.attrs.get('rows', 3)
                })
            elif isinstance(field.widget, (forms.DateInput, forms.DateTimeInput)):
                field.widget.attrs.update({
                    'class': f'{current_classes} w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs sm:text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors shadow-sm'.strip(),
                    'type': 'date'
                })
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs.update({
                    'class': f'{current_classes} w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer'.strip()
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': f'{current_classes} w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500'.strip()
                })
            else:
                field.widget.attrs.update({
                    'class': f'{current_classes} w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs sm:text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors placeholder:text-slate-400 shadow-sm'.strip()
                })


class EmployeeForm(forms.ModelForm):
    """Legacy Employee form preserved for backward compatibility with existing modals."""
    class Meta:
        model = Employee
        fields = ['pl_number', 'name', 'father_name', 'department', 'designation', 'joined_date']
        widgets = {
            'pl_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'PL-10020'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Muhammad Bilal'}),
            'father_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Tariq Mahmood'}),
            'department': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}, choices=[
                ('Mechanical Assembly', 'Mechanical Assembly'),
                ('Electrical Engineering', 'Electrical Engineering'),
                ('Quality Assurance', 'Quality Assurance'),
                ('Human Resources', 'Human Resources'),
                ('Logistics & Stores', 'Logistics & Stores'),
                ('Medical & Welfare', 'Medical & Welfare'),
                ('Finance & Accounts', 'Finance & Accounts'),
            ]),
            'designation': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Technician'}),
            'joined_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
        }


DEPARTMENT_CHOICES = [
    ('Mechanical Assembly', 'Mechanical Assembly'),
    ('Electrical Engineering', 'Electrical Engineering'),
    ('Quality Assurance', 'Quality Assurance'),
    ('Human Resources', 'Human Resources'),
    ('Logistics & Stores', 'Logistics & Stores'),
    ('Medical & Welfare', 'Medical & Welfare'),
    ('Finance & Accounts', 'Finance & Accounts'),
    ('Administration & Security', 'Administration & Security'),
    ('Information Technology', 'Information Technology'),
    ('Operations & Maintenance', 'Operations & Maintenance'),
]


class FullEmployeeForm(TailwindMixin, forms.ModelForm):
    """
    Comprehensive Employee Data Entry Form with all fields organized,
    proper validation, placeholders, and widget configurations.
    """
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'bg-white'})
    )

    class Meta:
        model = Employee
        exclude = ['created_at', 'updated_at']
        labels = {
            'pl_number': 'Employee ID / PL Number',
            'name': 'Employee Full Name',
            'father_name': 'Father / Guardian Name',
            'cnic': 'CNIC / National Identity Card Number',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'contact_number': 'Contact / Mobile Number',
            'email': 'Official / Personal Email Address',
            'address': 'Residential / Permanent Address',
            'department': 'Assigned Department',
            'designation': 'Current Job Designation / Title',
            'grade_scale': 'Pay Grade / Scale (e.g. BPS-16)',
            'joined_date': 'Date of Joining Service',
            'employment_status': 'Employment Status',
            'basic_salary': 'Basic Monthly Salary (Rs.)',
            'bank_name': 'Bank Name',
            'bank_account': 'Bank Account Number',
            'bank_iban': 'Bank IBAN Number',
            'emergency_contact_name': 'Emergency Contact Person Name',
            'emergency_contact_phone': 'Emergency Contact Phone Number',
            'emergency_contact_relation': 'Emergency Contact Relationship',
            'profile_picture': 'Employee Portrait / Profile Picture',
        }
        widgets = {
            'pl_number': forms.TextInput(attrs={'placeholder': 'e.g. PL-10452'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Muhammad Bilal Khan'}),
            'father_name': forms.TextInput(attrs={'placeholder': 'e.g. Tariq Mahmood Khan'}),
            'cnic': forms.TextInput(attrs={'placeholder': 'e.g. 37405-1234567-1'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'bg-white'}),
            'contact_number': forms.TextInput(attrs={'placeholder': 'e.g. +92 300 1234567'}),
            'email': forms.EmailInput(attrs={'placeholder': 'e.g. bilal.khan@factory.org'}),
            'address': forms.Textarea(attrs={'placeholder': 'Enter complete residential address, street, sector, city...', 'rows': 3}),
            'designation': forms.TextInput(attrs={'placeholder': 'e.g. Senior Electrical Technician'}),
            'grade_scale': forms.TextInput(attrs={'placeholder': 'e.g. Scale-14 / Grade B'}),
            'joined_date': forms.DateInput(attrs={'type': 'date'}),
            'employment_status': forms.Select(attrs={'class': 'bg-white'}),
            'basic_salary': forms.NumberInput(attrs={'placeholder': 'e.g. 75000', 'min': '0', 'step': '500'}),
            'bank_name': forms.TextInput(attrs={'placeholder': 'e.g. Habib Bank Limited (HBL)'}),
            'bank_account': forms.TextInput(attrs={'placeholder': 'e.g. 1024-79012345-03'}),
            'bank_iban': forms.TextInput(attrs={'placeholder': 'e.g. PK36HABB0000001024790103'}),
            'emergency_contact_name': forms.TextInput(attrs={'placeholder': 'e.g. Usman Tariq Khan'}),
            'emergency_contact_phone': forms.TextInput(attrs={'placeholder': 'e.g. +92 321 9876543'}),
            'emergency_contact_relation': forms.TextInput(attrs={'placeholder': 'e.g. Brother / Spouse / Father'}),
            'profile_picture': forms.ClearableFileInput(),
        }

    def clean_pl_number(self):
        pl = self.cleaned_data.get('pl_number', '').strip().upper()
        if not pl:
            raise forms.ValidationError('Employee PL Number / ID is required.')
        # Check uniqueness on update vs create
        qs = Employee.objects.filter(pl_number__iexact=pl)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'An employee with PL Number "{pl}" already exists.')
        return pl

    def clean_cnic(self):
        cnic = self.cleaned_data.get('cnic')
        if cnic:
            cnic = cnic.strip()
            qs = Employee.objects.filter(cnic=cnic)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'An employee with CNIC "{cnic}" already exists.')
        return cnic


class DependentForm(TailwindMixin, forms.ModelForm):
    """Form for adding and editing employee dependents / family members."""
    class Meta:
        model = Dependent
        exclude = ['employee', 'created_at']
        labels = {
            'name': 'Dependent Full Name',
            'relationship': 'Relationship to Employee',
            'gender': 'Gender',
            'date_of_birth': 'Date of Birth',
            'cnic_bform': 'CNIC / B-Form Number',
            'contact': 'Contact Number',
            'medical_eligible': 'Medical Welfare Eligible',
            'status': 'Status',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Fatima Bilal'}),
            'relationship': forms.Select(attrs={'class': 'bg-white'}),
            'gender': forms.Select(attrs={'class': 'bg-white'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'cnic_bform': forms.TextInput(attrs={'placeholder': 'e.g. 37405-7654321-2'}),
            'contact': forms.TextInput(attrs={'placeholder': 'e.g. +92 300 7654321'}),
            'medical_eligible': forms.CheckboxInput(),
            'status': forms.Select(attrs={'class': 'bg-white'}),
        }

from django import forms
from welfare_app.models import Employee, Dependent


class EmployeeForm(forms.ModelForm):
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
            ]),
            'designation': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'placeholder': 'Technician'}),
            'joined_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
        }


class TailwindMixin:
    """Mixin that auto-applies Tailwind CSS classes to all form fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm', 'rows': '3'})
            elif isinstance(field.widget, (forms.DateInput, forms.DateTimeInput)):
                field.widget.attrs.update({'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm', 'type': 'date'})
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs.update({'class': 'w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'rounded border-slate-300 text-blue-600 focus:ring-blue-500'})
            else:
                field.widget.attrs.update({'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm'})


class FullEmployeeForm(TailwindMixin, forms.ModelForm):
    """Comprehensive employee form with all fields for the full create/edit page."""
    class Meta:
        model = Employee
        exclude = ['created_at', 'updated_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joined_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class DependentForm(TailwindMixin, forms.ModelForm):
    """Form for adding/editing employee dependents."""
    class Meta:
        model = Dependent
        exclude = ['employee', 'created_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

from django import forms
from welfare_app.models import Bill
from .employee_forms import TailwindMixin


class BillForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Bill
        exclude = ['created_at', 'updated_at', 'created_by']
        widgets = {
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

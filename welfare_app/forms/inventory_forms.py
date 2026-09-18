from django import forms
from welfare_app.models import Medicine, MedicineTransaction
from .employee_forms import TailwindMixin


class MedicineForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Medicine
        exclude = ['created_at', 'updated_at']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }


class MedicineTransactionForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = MedicineTransaction
        exclude = ['created_by', 'created_at', 'transaction_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

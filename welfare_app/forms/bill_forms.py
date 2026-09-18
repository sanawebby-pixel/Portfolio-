from django import forms
from welfare_app.models import Bill, Hospital, Employee
from .employee_forms import TailwindMixin


class BillForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Bill
        exclude = ['created_at', 'updated_at', 'created_by']
        labels = {
            'bill_number': 'Invoice / Bill / Voucher #',
            'bill_date': 'Invoice / Bill Date',
            'category': 'Expense Category',
            'hospital': 'Hospital / Clinic (If panel invoice)',
            'vendor_name': 'Vendor / Hospital / Payee Name',
            'employee': 'Associated Employee (If personal reimbursement)',
            'amount': 'Bill / Expense Amount (Rs.)',
            'due_date': 'Payment Due Date',
            'status': 'Approval Status',
            'payment_status': 'Payment Status',
            'payment_method': 'Payment Method',
            'attachment': 'Attach Invoice / Bill Copy (PDF/JPG)',
            'paid_date': 'Date Paid',
            'description': 'Description / Item Details',
        }
        widgets = {
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
            'bill_number': forms.TextInput(attrs={'placeholder': 'e.g. INV-2026-8801'}),
            'vendor_name': forms.TextInput(attrs={'placeholder': 'e.g. Al-Shifa Hospital Billing Dept.'}),
            'amount': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'font-mono text-base font-bold'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter monthly panel hospital consolidated billing details or expense reason...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hospital'].queryset = Hospital.objects.all().order_by('name')
        self.fields['employee'].queryset = Employee.objects.all().order_by('name')

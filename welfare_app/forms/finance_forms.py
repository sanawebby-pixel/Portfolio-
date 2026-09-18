from django import forms
from welfare_app.models import Budget, FinanceTransaction, Department, MedicalClaim
from .employee_forms import TailwindMixin


class BudgetForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Budget
        exclude = ['created_at']
        labels = {
            'year': 'Fiscal / Financial Year',
            'department': 'Department (Leave empty for Organization-wide fund)',
            'category': 'Budget Category / Fund Type',
            'allocated_amount': 'Allocated Budget Amount (Rs.)',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'is_active': 'Budget Status',
            'description': 'Budget Description & Notes',
        }
        widgets = {
            'year': forms.NumberInput(attrs={'placeholder': '2026', 'min': '2020', 'max': '2050'}),
            'allocated_amount': forms.NumberInput(attrs={'placeholder': 'e.g. 1500000', 'min': '0', 'step': '1000', 'class': 'font-mono text-base font-bold text-blue-600'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Annual medical welfare allocation approved by Board of Trustees...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')


class FinanceTransactionForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = FinanceTransaction
        exclude = ['transaction_id', 'created_by', 'created_at']
        labels = {
            'transaction_type': 'Transaction Type',
            'amount': 'Transaction Amount (Rs.)',
            'category': 'Category / Account Head',
            'date': 'Transaction Date',
            'payment_method': 'Payment / Transfer Method',
            'account': 'Bank / Cash Account',
            'reference_number': 'Reference / Cheque / Tx #',
            'related_claim': 'Linked Medical Claim (Optional)',
            'attachment': 'Attach Voucher / Bank Deposit Slip',
            'description': 'Transaction Description & Justification',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'font-mono text-base font-bold'}),
            'category': forms.TextInput(attrs={'placeholder': 'e.g. Factory Monthly Welfare Grant / Direct Hospital Payment'}),
            'account': forms.TextInput(attrs={'placeholder': 'e.g. Welfare Main Treasury HBL A/C 0042'}),
            'reference_number': forms.TextInput(attrs={'placeholder': 'e.g. CHQ-991204 / TRF-88129'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter complete transaction description...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['related_claim'].queryset = MedicalClaim.objects.all().order_by('-id')[:50]

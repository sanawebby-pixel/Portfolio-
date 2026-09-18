from django import forms
from welfare_app.models import Budget, FinanceTransaction
from .employee_forms import TailwindMixin


class BudgetForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Budget
        exclude = ['created_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class FinanceTransactionForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = FinanceTransaction
        exclude = ['created_by', 'created_at']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

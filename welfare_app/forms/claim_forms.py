from django import forms
from django.forms import inlineformset_factory
from welfare_app.models import MedicalClaim, ClaimExpenseItem
from .employee_forms import TailwindMixin


class MedicalClaimForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = MedicalClaim
        exclude = ['claim_number', 'created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'claim_date': forms.DateInput(attrs={'type': 'date'}),
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }


class ClaimExpenseItemForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = ClaimExpenseItem
        exclude = ['claim', 'created_at']


ClaimExpenseItemFormSet = inlineformset_factory(
    MedicalClaim,
    ClaimExpenseItem,
    form=ClaimExpenseItemForm,
    extra=3,
    can_delete=True,
)

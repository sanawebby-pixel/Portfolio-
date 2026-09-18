from django import forms
from django.forms import inlineformset_factory
from welfare_app.models import MedicalClaim, ClaimExpenseItem, ClaimPayment, ApprovalWorkflow, Employee, Hospital, Doctor
from .employee_forms import TailwindMixin


class MedicalClaimForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = MedicalClaim
        exclude = ['claim_number', 'paid_amount', 'created_by', 'updated_by', 'created_at', 'updated_at']
        labels = {
            'employee': 'Employee (Search / Select)',
            'dependent': 'Family Member / Patient (Optional - Leave blank if for Employee)',
            'hospital_visit': 'Linked Hospital Consultation (Optional)',
            'hospital': 'Hospital / Clinic',
            'doctor': 'Attending Doctor',
            'claim_type': 'Medical Claim Category',
            'claim_date': 'Claim Submission Date',
            'treatment_date': 'Date of Treatment',
            'diagnosis': 'Medical Diagnosis / Reason for Claim',
            'bill_number': 'Hospital / Clinic Bill #',
            'bill_date': 'Bill Date',
            'doctor_fee': 'Doctor / Consultation Fee (Rs.)',
            'doctor_dues': 'Doctor / Hospital Dues (Rs.)',
            'lab_fee': 'Laboratory & Diagnostics Cost (Rs.)',
            'medicine_fee': 'Prescription Medicine Cost (Rs.)',
            'admission_fee': 'Hospital Admission & Bed Cost (Rs.)',
            'procedure_fee': 'Surgical / Medical Procedure Cost (Rs.)',
            'other_fee': 'Other Incidental Charges (Rs.)',
            'employee_contribution': 'Employee Co-Payment / Deductible (Rs.)',
            'welfare_contribution': 'Welfare Fund Contribution (Rs.)',
            'claimable_amount': 'Total Claimable Amount (Rs.)',
            'approved_amount': 'Approved Amount (Rs.)',
            'claim_status': 'Claim Approval Status',
            'payment_status': 'Payment Disbursement Status',
            'supporting_documents': 'Supporting Documents / Bill & Prescription Scans',
            'remarks': 'Employee / Welfare Officer Remarks',
        }
        widgets = {
            'claim_date': forms.DateInput(attrs={'type': 'date'}),
            'treatment_date': forms.DateInput(attrs={'type': 'date'}),
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
            'diagnosis': forms.TextInput(attrs={'placeholder': 'e.g. Acute Typhoid with Gastrointestinal Complications'}),
            'bill_number': forms.TextInput(attrs={'placeholder': 'e.g. INV-2026-9901'}),
            'doctor_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'fee-input font-mono'}),
            'doctor_dues': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'fee-input font-mono'}),
            'lab_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'fee-input font-mono'}),
            'medicine_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'fee-input font-mono'}),
            'admission_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'fee-input font-mono'}),
            'procedure_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'fee-input font-mono'}),
            'other_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'fee-input font-mono'}),
            'employee_contribution': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'font-mono'}),
            'welfare_contribution': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'font-mono'}),
            'claimable_amount': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'font-mono'}),
            'approved_amount': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '10', 'class': 'font-mono'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter justification, policy reference, or special approval notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.all().order_by('name')
        self.fields['hospital'].queryset = Hospital.objects.filter(status='Active').order_by('name')
        self.fields['doctor'].queryset = Doctor.objects.filter(status='Active').order_by('name')
        # Default safety: New claims start as Pending and Unpaid
        if not self.instance or not self.instance.pk:
            self.fields['claim_status'].initial = 'Pending'
            self.fields['payment_status'].initial = 'Unpaid'


class ClaimPaymentForm(TailwindMixin, forms.ModelForm):
    """Form to disburse payments against approved claims."""
    class Meta:
        model = ClaimPayment
        fields = ['payment_amount', 'payment_date', 'payment_method', 'account', 'transaction_reference', 'receipt_attachment', 'remarks']
        labels = {
            'payment_amount': 'Payment Amount to Disburse (Rs.)',
            'payment_date': 'Disbursement / Cheque Date',
            'payment_method': 'Disbursement Method',
            'account': 'Funding / Treasury Account',
            'transaction_reference': 'Cheque / Bank Reference #',
            'receipt_attachment': 'Attach Bank Slip / Payment Voucher',
            'remarks': 'Payment Notes',
        }
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_amount': forms.NumberInput(attrs={'min': '1', 'step': '1', 'placeholder': 'e.g. 8500', 'class': 'font-mono text-base font-bold text-emerald-600'}),
            'account': forms.TextInput(attrs={'placeholder': 'e.g. Welfare Main Account (HBL A/C 0042-7901)'}),
            'transaction_reference': forms.TextInput(attrs={'placeholder': 'e.g. CHQ-991203 / FT-887102'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Direct online transfer to employee salary bank account...'}),
        }


class ClaimApprovalForm(TailwindMixin, forms.Form):
    """Form for approving, partially approving, or rejecting a claim."""
    action = forms.ChoiceField(
        choices=[
            ('Approved', 'Approve Full Claim'),
            ('Partially Approved', 'Approve Partial Amount'),
            ('Rejected', 'Reject Claim'),
            ('Returned', 'Return for Correction'),
        ],
        widget=forms.Select(attrs={'class': 'font-bold'})
    )
    approved_amount = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Approved amount (Rs.)', 'class': 'font-mono'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter approval justification, policy scale reference, or rejection reason...'})
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        remarks = cleaned_data.get('remarks')
        approved_amount = cleaned_data.get('approved_amount')

        if action == 'Rejected' and not remarks:
            raise forms.ValidationError('A detailed rejection reason is mandatory when rejecting a claim.')
        if action == 'Partially Approved' and (approved_amount is None or approved_amount <= 0):
            raise forms.ValidationError('Please specify the partial approved amount in Rs.')
        return cleaned_data


class ClaimExpenseItemForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = ClaimExpenseItem
        exclude = ['claim', 'created_at']


ClaimExpenseItemFormSet = inlineformset_factory(
    MedicalClaim,
    ClaimExpenseItem,
    form=ClaimExpenseItemForm,
    extra=2,
    can_delete=True,
)

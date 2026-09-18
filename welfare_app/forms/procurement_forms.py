from django import forms
from welfare_app.models import Supplier, PurchaseRequest, PurchaseOrder
from .employee_forms import TailwindMixin


class SupplierForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        exclude = ['created_at']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class PurchaseRequestForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        exclude = ['request_number', 'requester', 'approved_by', 'approved_date', 'created_at', 'updated_at']
        widgets = {
            'items_description': forms.Textarea(attrs={'rows': 4}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }


class PurchaseOrderForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        exclude = ['order_number', 'created_by', 'created_at', 'updated_at']
        widgets = {
            'items_description': forms.Textarea(attrs={'rows': 4}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'expected_delivery': forms.DateInput(attrs={'type': 'date'}),
            'actual_delivery': forms.DateInput(attrs={'type': 'date'}),
        }

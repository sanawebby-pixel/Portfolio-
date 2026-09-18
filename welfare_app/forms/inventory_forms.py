from django import forms
from welfare_app.models import Medicine, MedicineTransaction, Supplier
from .employee_forms import TailwindMixin


class MedicineForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Medicine
        exclude = ['medicine_id', 'created_at', 'updated_at']
        labels = {
            'name': 'Medicine Brand / Trade Name',
            'generic_name': 'Generic Formula / Chemical Name',
            'category': 'Dosage Form / Category',
            'manufacturer': 'Pharmaceutical Manufacturer',
            'batch_number': 'Batch / Lot Number',
            'expiry_date': 'Expiry Date',
            'unit': 'Unit of Measure',
            'unit_cost': 'Unit Cost / Purchase Price (Rs.)',
            'selling_price': 'Standard MRP / Price (Rs.)',
            'quantity': 'Initial Stock Quantity',
            'min_stock_level': 'Minimum Safety Stock Threshold',
            'supplier': 'Preferred Supplier / Distributor',
            'is_active': 'Active in Formulary',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Panadol Extra 500mg'}),
            'generic_name': forms.TextInput(attrs={'placeholder': 'e.g. Paracetamol + Caffeine'}),
            'manufacturer': forms.TextInput(attrs={'placeholder': 'e.g. GSK Pakistan Ltd.'}),
            'batch_number': forms.TextInput(attrs={'placeholder': 'e.g. BATCH-8890'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'unit_cost': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '0.1', 'class': 'font-mono'}),
            'selling_price': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0', 'step': '0.1', 'class': 'font-mono'}),
            'quantity': forms.NumberInput(attrs={'placeholder': '0', 'min': '0'}),
            'min_stock_level': forms.NumberInput(attrs={'placeholder': '10', 'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(status='Active').order_by('name')


class MedicineTransactionForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = MedicineTransaction
        exclude = ['created_by', 'created_at']
        labels = {
            'medicine': 'Select Medicine',
            'transaction_type': 'Stock Action',
            'quantity': 'Quantity (Units/Packs)',
            'reference': 'Reference / Invoice / Rx #',
            'date': 'Transaction Date',
            'notes': 'Stock Adjustment Notes / Reason',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'e.g. 50', 'min': '1'}),
            'reference': forms.TextInput(attrs={'placeholder': 'e.g. PO-0012 / Dispense-PL1002'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Received from distributor / Issued for factory emergency box...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medicine'].queryset = Medicine.objects.filter(is_active=True).order_by('name')

import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum
from django.utils import timezone

from ..models import Medicine, MedicineTransaction, Supplier, AuditLog
from ..forms.inventory_forms import MedicineForm, MedicineTransactionForm


@login_required
def medicine_list(request):
    """List, search, filter, and monitor medicine formulary & stock thresholds."""
    today = timezone.now().date()
    exp_threshold = today + datetime.timedelta(days=90)

    medicines = Medicine.objects.select_related('supplier').all()

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    stock_status = request.GET.get('stock', '').strip()
    supplier_id = request.GET.get('supplier', '').strip()

    # Search
    if q:
        medicines = medicines.filter(
            Q(name__icontains=q) |
            Q(generic_name__icontains=q) |
            Q(batch_number__icontains=q) |
            Q(manufacturer__icontains=q) |
            Q(medicine_id__icontains=q)
        )

    # Filter Category
    if category:
        medicines = medicines.filter(category=category)

    # Filter Supplier
    if supplier_id:
        medicines = medicines.filter(supplier_id=supplier_id)

    # Filter Stock & Expiry Status
    if stock_status == 'low':
        medicines = medicines.filter(quantity__lte=F('min_stock_level'))
    elif stock_status == 'out_of_stock':
        medicines = medicines.filter(quantity__lte=0)
    elif stock_status == 'expired':
        medicines = medicines.filter(expiry_date__lt=today)
    elif stock_status == 'expiring':
        medicines = medicines.filter(expiry_date__gte=today, expiry_date__lte=exp_threshold)
    elif stock_status == 'in_stock':
        medicines = medicines.filter(quantity__gt=F('min_stock_level'))

    # Overall KPIs
    all_meds = Medicine.objects.all()
    total_count = all_meds.count()
    total_units = all_meds.aggregate(total=Sum('quantity'))['total'] or 0

    # Stock value calculation (Python iteration to handle unit_cost fallback)
    total_stock_value = sum(m.stock_value for m in all_meds)

    low_stock_count = all_meds.filter(quantity__lte=F('min_stock_level'), is_active=True).count()
    out_of_stock_count = all_meds.filter(quantity__lte=0, is_active=True).count()
    expiring_count = all_meds.filter(expiry_date__gte=today, expiry_date__lte=exp_threshold, is_active=True).count()
    expired_count = all_meds.filter(expiry_date__lt=today, is_active=True).count()

    stats = {
        'total_count': total_count,
        'total_units': total_units,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'expiring_count': expiring_count,
        'expired_count': expired_count,
    }

    suppliers = Supplier.objects.filter(status='Active').order_by('name')
    categories = Medicine.CATEGORY_CHOICES

    paginator = Paginator(medicines.order_by('name'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/inventory/medicines.html', {
        'page_obj': page_obj,
        'q': q,
        'category': category,
        'stock_status': stock_status,
        'supplier_id': supplier_id,
        'stats': stats,
        'suppliers': suppliers,
        'categories': categories,
        'active_nav': 'medicines',
    })


@login_required
def medicine_create(request):
    """Add a new Medicine to the Pharmacy formulary."""
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            med = form.save()
            AuditLog.log(
                user=request.user,
                action='Created',
                module='Medicine',
                record_id=str(med.pk),
                record_repr=f"Medicine {med.name} ({med.medicine_id})",
                new_values={'name': med.name, 'quantity': med.quantity, 'category': med.category},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Medicine "{med.name}" ({med.medicine_id}) added to formulary.')
            return redirect('medicine_list')
        else:
            messages.error(request, 'Please resolve the highlighted errors in the medicine form.')
    else:
        form = MedicineForm(initial={'quantity': 0, 'min_stock_level': 10, 'unit': 'Pack', 'is_active': True})

    return render(request, 'welfare_app/inventory/medicine_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'medicines',
    })


@login_required
def medicine_update(request, pk):
    """Edit Medicine formulary and safety thresholds."""
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            updated_med = form.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='Medicine',
                record_id=str(medicine.pk),
                record_repr=f"Medicine {medicine.name}",
                new_values={'quantity': updated_med.quantity, 'unit_cost': str(updated_med.unit_cost)},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Medicine "{medicine.name}" updated successfully.')
            return redirect('medicine_list')
        else:
            messages.error(request, 'Please correct the highlighted errors.')
    else:
        form = MedicineForm(instance=medicine)

    return render(request, 'welfare_app/inventory/medicine_form.html', {
        'form': form,
        'medicine': medicine,
        'is_edit': True,
        'active_nav': 'medicines',
    })


@login_required
def medicine_delete(request, pk):
    """Delete a medicine record from inventory."""
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        med_name = medicine.name
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='Medicine',
            record_id=str(medicine.pk),
            record_repr=f"Medicine {med_name}",
            ip_address=getattr(request, 'client_ip', None)
        )
        medicine.delete()
        messages.success(request, f'Medicine "{med_name}" removed from inventory.')
    return redirect('medicine_list')


@login_required
def stock_transactions(request):
    """Stock movement ledger (Stock In, Stock Out, Adjustments)."""
    transactions = MedicineTransaction.objects.select_related('medicine', 'created_by').all()

    q = request.GET.get('q', '').strip()
    tx_type = request.GET.get('type', '').strip()
    medicine_id = request.GET.get('medicine', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if q:
        transactions = transactions.filter(
            Q(reference__icontains=q) |
            Q(notes__icontains=q) |
            Q(medicine__name__icontains=q) |
            Q(medicine__medicine_id__icontains=q)
        )
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    if medicine_id:
        transactions = transactions.filter(medicine_id=medicine_id)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    # KPIs
    all_tx = MedicineTransaction.objects.all()
    total_count = all_tx.count()
    total_in = all_tx.filter(transaction_type='Stock In').aggregate(total=Sum('quantity'))['total'] or 0
    total_out = all_tx.filter(transaction_type='Stock Out').aggregate(total=Sum('quantity'))['total'] or 0
    total_adjustments = all_tx.filter(transaction_type='Adjustment').count()

    stats = {
        'total_count': total_count,
        'total_in': total_in,
        'total_out': total_out,
        'total_adjustments': total_adjustments,
    }

    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    types = MedicineTransaction.TYPE_CHOICES

    paginator = Paginator(transactions.order_by('-date', '-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/inventory/stock.html', {
        'page_obj': page_obj,
        'q': q,
        'tx_type': tx_type,
        'medicine_id': medicine_id,
        'date_from': date_from,
        'date_to': date_to,
        'stats': stats,
        'medicines': medicines,
        'types': types,
        'active_nav': 'medicines',
    })


@login_required
def stock_in(request):
    """Receive inventory stock (Receipt / Purchase)."""
    if request.method == 'POST':
        form = MedicineTransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.transaction_type = 'Stock In'
            tx.created_by = request.user
            tx.save()

            AuditLog.log(
                user=request.user,
                action='Stock In',
                module='Medicine',
                record_id=str(tx.medicine.pk),
                record_repr=f"Stock In +{tx.quantity} {tx.medicine.name}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Added {tx.quantity} units of {tx.medicine.name} to inventory.')
            return redirect('stock_transactions')
        else:
            messages.error(request, 'Please correct the highlighted errors.')
    else:
        med_id = request.GET.get('medicine')
        initial = {'date': timezone.now().date(), 'transaction_type': 'Stock In'}
        if med_id:
            initial['medicine'] = med_id
        form = MedicineTransactionForm(initial=initial)

    return render(request, 'welfare_app/inventory/stock_form.html', {
        'form': form,
        'transaction_type': 'Stock In',
        'active_nav': 'medicines',
    })


@login_required
def stock_out(request):
    """Dispense inventory stock to factory clinic / employee."""
    if request.method == 'POST':
        form = MedicineTransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.transaction_type = 'Stock Out'
            tx.created_by = request.user

            # Check stock availability
            if tx.medicine.quantity < tx.quantity:
                messages.warning(request, f'Warning: Available stock ({tx.medicine.quantity}) was less than requested quantity ({tx.quantity}). Stock is now zero.')

            tx.save()

            AuditLog.log(
                user=request.user,
                action='Stock Out',
                module='Medicine',
                record_id=str(tx.medicine.pk),
                record_repr=f"Stock Out -{tx.quantity} {tx.medicine.name}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Dispensed {tx.quantity} units of {tx.medicine.name}.')
            return redirect('stock_transactions')
        else:
            messages.error(request, 'Please correct the highlighted errors.')
    else:
        med_id = request.GET.get('medicine')
        initial = {'date': timezone.now().date(), 'transaction_type': 'Stock Out'}
        if med_id:
            initial['medicine'] = med_id
        form = MedicineTransactionForm(initial=initial)

    return render(request, 'welfare_app/inventory/stock_form.html', {
        'form': form,
        'transaction_type': 'Stock Out',
        'active_nav': 'medicines',
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.utils import timezone
from ..models import Medicine, MedicineTransaction, AuditLog
from ..forms.inventory_forms import MedicineForm, MedicineTransactionForm


@login_required
def medicine_list(request):
    medicines = Medicine.objects.all()
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    stock_filter = request.GET.get('stock', '')
    
    if q:
        medicines = medicines.filter(Q(name__icontains=q) | Q(generic_name__icontains=q))
    if category:
        medicines = medicines.filter(category=category)
    if stock_filter == 'low':
        medicines = medicines.filter(quantity__lte=F('min_stock_level'))
    elif stock_filter == 'expired':
        medicines = medicines.filter(expiry_date__lt=timezone.now().date())
    elif stock_filter == 'expiring':
        from datetime import timedelta
        medicines = medicines.filter(
            expiry_date__lte=timezone.now().date() + timedelta(days=90),
            expiry_date__gte=timezone.now().date()
        )
    
    low_stock_count = Medicine.objects.filter(quantity__lte=F('min_stock_level'), is_active=True).count()
    expiring_count = Medicine.objects.filter(
        expiry_date__lte=timezone.now().date() + __import__('datetime').timedelta(days=90),
        expiry_date__gte=timezone.now().date(), is_active=True
    ).count()
    
    paginator = Paginator(medicines.order_by('name'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'welfare_app/inventory/medicines.html', {
        'page_obj': page_obj, 'q': q, 'category': category, 'stock_filter': stock_filter,
        'low_stock_count': low_stock_count, 'expiring_count': expiring_count,
        'active_nav': 'medicines',
    })


@login_required
def medicine_create(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine added.')
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'welfare_app/inventory/medicine_form.html', {'form': form, 'active_nav': 'medicines'})


@login_required
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f'{medicine.name} updated.')
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'welfare_app/inventory/medicine_form.html', {'form': form, 'medicine': medicine, 'active_nav': 'medicines'})


@login_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        medicine.delete()
        messages.success(request, 'Medicine deleted.')
    return redirect('medicine_list')


@login_required
def stock_transactions(request):
    transactions = MedicineTransaction.objects.select_related('medicine').all()
    paginator = Paginator(transactions.order_by('-created_at'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'welfare_app/inventory/stock.html', {
        'page_obj': page_obj, 'active_nav': 'medicines',
    })


@login_required
def stock_in(request):
    if request.method == 'POST':
        form = MedicineTransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.transaction_type = 'Stock In'
            tx.created_by = request.user
            tx.save()
            messages.success(request, 'Stock added.')
            return redirect('stock_transactions')
    else:
        form = MedicineTransactionForm()
    return render(request, 'welfare_app/inventory/stock_form.html', {
        'form': form, 'transaction_type': 'Stock In', 'active_nav': 'medicines',
    })


@login_required
def stock_out(request):
    if request.method == 'POST':
        form = MedicineTransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.transaction_type = 'Stock Out'
            tx.created_by = request.user
            tx.save()
            messages.success(request, 'Stock issued.')
            return redirect('stock_transactions')
    else:
        form = MedicineTransactionForm()
    return render(request, 'welfare_app/inventory/stock_form.html', {
        'form': form, 'transaction_type': 'Stock Out', 'active_nav': 'medicines',
    })

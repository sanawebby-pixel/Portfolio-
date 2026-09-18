from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Supplier, PurchaseRequest, PurchaseOrder, AuditLog
from ..forms.procurement_forms import SupplierForm, PurchaseRequestForm, PurchaseOrderForm


@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    q = request.GET.get('q', '')
    if q:
        from django.db.models import Q
        suppliers = suppliers.filter(Q(name__icontains=q) | Q(contact_person__icontains=q))
    paginator = Paginator(suppliers.order_by('name'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'welfare_app/procurement/suppliers.html', {
        'page_obj': page_obj, 'q': q, 'active_nav': 'suppliers',
    })


@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added.')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'welfare_app/procurement/supplier_form.html', {'form': form, 'active_nav': 'suppliers'})


@login_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated.')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'welfare_app/procurement/supplier_form.html', {'form': form, 'supplier': supplier, 'active_nav': 'suppliers'})


@login_required
def purchase_request_list(request):
    prs = PurchaseRequest.objects.select_related('requester', 'department').all()
    paginator = Paginator(prs.order_by('-created_at'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'welfare_app/procurement/requests.html', {
        'page_obj': page_obj, 'active_nav': 'procurement',
    })


@login_required
def purchase_request_create(request):
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            pr = form.save(commit=False)
            pr.requester = request.user
            pr.save()
            messages.success(request, f'Purchase Request {pr.request_number} created.')
            return redirect('purchase_request_list')
    else:
        form = PurchaseRequestForm()
    return render(request, 'welfare_app/procurement/request_form.html', {'form': form, 'active_nav': 'procurement'})


@login_required
def purchase_request_approve(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'approve')
        if action == 'approve':
            pr.status = 'Approved'
            pr.approved_by = request.user
            from django.utils import timezone
            pr.approved_date = timezone.now()
        elif action == 'reject':
            pr.status = 'Rejected'
        pr.save()
        messages.success(request, f'PR {pr.request_number} {action}d.')
    return redirect('purchase_request_list')


@login_required
def purchase_order_list(request):
    pos = PurchaseOrder.objects.select_related('supplier').all()
    paginator = Paginator(pos.order_by('-created_at'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'welfare_app/procurement/orders.html', {
        'page_obj': page_obj, 'active_nav': 'procurement',
    })


@login_required
def purchase_order_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            messages.success(request, f'Purchase Order {po.order_number} created.')
            return redirect('purchase_order_list')
    else:
        form = PurchaseOrderForm()
    return render(request, 'welfare_app/procurement/order_form.html', {'form': form, 'active_nav': 'procurement'})

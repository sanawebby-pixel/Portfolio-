from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone

from ..models import Supplier, PurchaseRequest, PurchaseOrder, Department, AuditLog
from ..forms.procurement_forms import SupplierForm, PurchaseRequestForm, PurchaseOrderForm


# ============================================================
# Suppliers Master Data
# ============================================================

@login_required
def supplier_list(request):
    """List, search, and manage registered pharmaceutical and medical suppliers."""
    suppliers = Supplier.objects.all()

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    category = request.GET.get('category', '').strip()

    if q:
        suppliers = suppliers.filter(
            Q(name__icontains=q) |
            Q(supplier_id__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(city__icontains=q) |
            Q(ntn_registration__icontains=q)
        )
    if status:
        suppliers = suppliers.filter(status=status)
    if category:
        suppliers = suppliers.filter(category__icontains=category)

    # Supplier KPIs
    all_suppliers = Supplier.objects.all()
    total_suppliers = all_suppliers.count()
    active_suppliers = all_suppliers.filter(status='Active').count()

    po_aggregate = PurchaseOrder.objects.aggregate(
        total_pos=Count('id'),
        total_spend=Sum('total_amount')
    )
    total_pos = po_aggregate['total_pos'] or 0
    total_spend = po_aggregate['total_spend'] or 0

    stats = {
        'total_suppliers': total_suppliers,
        'active_suppliers': active_suppliers,
        'total_pos': total_pos,
        'total_spend': total_spend,
    }

    paginator = Paginator(suppliers.order_by('name'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/procurement/suppliers.html', {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'category': category,
        'stats': stats,
        'active_nav': 'suppliers',
    })


@login_required
def supplier_create(request):
    """Register a new vendor/supplier."""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            sup = form.save()
            AuditLog.log(
                user=request.user,
                action='Created',
                module='Supplier',
                record_id=str(sup.pk),
                record_repr=f"Supplier {sup.name} ({sup.supplier_id})",
                new_values={'name': sup.name, 'city': sup.city},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Supplier "{sup.name}" ({sup.supplier_id}) added.')
            return redirect('supplier_list')
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = SupplierForm(initial={'status': 'Active', 'payment_terms': 'Net 30 Days'})

    return render(request, 'welfare_app/procurement/supplier_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'suppliers',
    })


@login_required
def supplier_update(request, pk):
    """Edit supplier details."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            updated = form.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='Supplier',
                record_id=str(supplier.pk),
                record_repr=f"Supplier {supplier.name}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Supplier "{supplier.name}" updated.')
            return redirect('supplier_list')
        else:
            messages.error(request, 'Please review the errors.')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'welfare_app/procurement/supplier_form.html', {
        'form': form,
        'supplier': supplier,
        'is_edit': True,
        'active_nav': 'suppliers',
    })


@login_required
def supplier_delete(request, pk):
    """Delete a supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        sup_name = supplier.name
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='Supplier',
            record_id=str(supplier.pk),
            record_repr=f"Supplier {sup_name}",
            ip_address=getattr(request, 'client_ip', None)
        )
        supplier.delete()
        messages.success(request, f'Supplier "{sup_name}" deleted.')
    return redirect('supplier_list')


# ============================================================
# Purchase Requests (PRs)
# ============================================================

@login_required
def purchase_request_list(request):
    """List and manage internal purchase requisitions."""
    prs = PurchaseRequest.objects.select_related('requester', 'department', 'supplier', 'approved_by').all()

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    dept_id = request.GET.get('department', '').strip()

    if q:
        prs = prs.filter(
            Q(request_number__icontains=q) |
            Q(item_name__icontains=q) |
            Q(items_description__icontains=q) |
            Q(reason__icontains=q) |
            Q(requester__username__icontains=q)
        )
    if status:
        prs = prs.filter(status=status)
    if priority:
        prs = prs.filter(priority=priority)
    if dept_id:
        prs = prs.filter(department_id=dept_id)

    # PR KPIs
    all_prs = PurchaseRequest.objects.all()
    total_count = all_prs.count()
    total_estimated_amount = all_prs.aggregate(total=Sum('estimated_amount'))['total'] or 0

    pending_prs = all_prs.filter(status='Pending Approval')
    pending_count = pending_prs.count()
    pending_amount = pending_prs.aggregate(total=Sum('estimated_amount'))['total'] or 0

    approved_prs = all_prs.filter(status__in=['Approved', 'Ordered', 'Completed'])
    approved_count = approved_prs.count()
    approved_amount = approved_prs.aggregate(total=Sum('estimated_amount'))['total'] or 0

    urgent_count = all_prs.filter(priority__in=['Urgent', 'Emergency'], status='Pending Approval').count()

    stats = {
        'total_count': total_count,
        'total_estimated_amount': total_estimated_amount,
        'pending_count': pending_count,
        'pending_amount': pending_amount,
        'approved_count': approved_count,
        'approved_amount': approved_amount,
        'urgent_count': urgent_count,
    }

    departments = Department.objects.filter(is_active=True).order_by('name')
    status_choices = PurchaseRequest.STATUS_CHOICES
    priority_choices = PurchaseRequest.PRIORITY_CHOICES

    paginator = Paginator(prs.order_by('-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/procurement/requests.html', {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'priority': priority,
        'dept_id': dept_id,
        'stats': stats,
        'departments': departments,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'active_nav': 'procurement',
    })


@login_required
def purchase_request_create(request):
    """Create a new Purchase Requisition."""
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST, request.FILES)
        if form.is_valid():
            pr = form.save(commit=False)
            pr.requester = request.user
            pr.save()

            AuditLog.log(
                user=request.user,
                action='Created',
                module='PurchaseRequest',
                record_id=str(pr.pk),
                record_repr=f"PR #{pr.request_number} ({pr.item_name})",
                new_values={'request_number': pr.request_number, 'amount': str(pr.estimated_amount)},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Purchase Request #{pr.request_number} submitted for review.')
            return redirect('purchase_request_list')
        else:
            messages.error(request, 'Please correct the highlighted form errors.')
    else:
        form = PurchaseRequestForm(initial={'priority': 'Normal', 'status': 'Pending Approval', 'quantity': 1})

    return render(request, 'welfare_app/procurement/request_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'procurement',
    })


@login_required
def purchase_request_update(request, pk):
    """Edit a Purchase Requisition."""
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST, request.FILES, instance=pr)
        if form.is_valid():
            updated = form.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='PurchaseRequest',
                record_id=str(pr.pk),
                record_repr=f"PR #{pr.request_number}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Purchase Request #{pr.request_number} updated.')
            return redirect('purchase_request_list')
        else:
            messages.error(request, 'Please review the errors below.')
    else:
        form = PurchaseRequestForm(instance=pr)

    return render(request, 'welfare_app/procurement/request_form.html', {
        'form': form,
        'pr': pr,
        'is_edit': True,
        'active_nav': 'procurement',
    })


@login_required
def purchase_request_delete(request, pk):
    """Delete a Purchase Requisition."""
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == 'POST':
        pr_num = pr.request_number
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='PurchaseRequest',
            record_id=str(pr.pk),
            record_repr=f"PR #{pr_num}",
            ip_address=getattr(request, 'client_ip', None)
        )
        pr.delete()
        messages.success(request, f'Purchase Request #{pr_num} deleted.')
    return redirect('purchase_request_list')


@login_required
def purchase_request_approve(request, pk):
    """Approve or Reject a Purchase Requisition."""
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'approve').lower()
        if action == 'approve':
            pr.status = 'Approved'
            pr.approved_by = request.user
            pr.approved_date = timezone.now().date()
            messages.success(request, f'Purchase Request #{pr.request_number} has been approved.')
        elif action == 'reject':
            pr.status = 'Rejected'
            messages.warning(request, f'Purchase Request #{pr.request_number} marked as Rejected.')
        elif action == 'order':
            pr.status = 'Ordered'
            messages.info(request, f'Purchase Request #{pr.request_number} marked as Ordered.')
        
        pr.save()

        AuditLog.log(
            user=request.user,
            action=action.title(),
            module='PurchaseRequest',
            record_id=str(pr.pk),
            record_repr=f"PR #{pr.request_number} -> {action}",
            ip_address=getattr(request, 'client_ip', None)
        )
    return redirect('purchase_request_list')


# ============================================================
# Purchase Orders (POs)
# ============================================================

@login_required
def purchase_order_list(request):
    """List, track fulfillment, and manage Purchase Orders."""
    pos = PurchaseOrder.objects.select_related('supplier', 'purchase_request', 'created_by').all()

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    payment = request.GET.get('payment', '').strip()
    supplier_id = request.GET.get('supplier', '').strip()

    if q:
        pos = pos.filter(
            Q(order_number__icontains=q) |
            Q(items_description__icontains=q) |
            Q(supplier__name__icontains=q) |
            Q(purchase_request__request_number__icontains=q)
        )
    if status:
        pos = pos.filter(status=status)
    if payment:
        pos = pos.filter(payment_status=payment)
    if supplier_id:
        pos = pos.filter(supplier_id=supplier_id)

    # PO KPIs
    all_pos = PurchaseOrder.objects.all()
    total_count = all_pos.count()
    total_amount = all_pos.aggregate(total=Sum('total_amount'))['total'] or 0

    open_pos = all_pos.filter(status__in=['Draft', 'Ordered', 'Acknowledged'])
    open_count = open_pos.count()
    open_amount = open_pos.aggregate(total=Sum('total_amount'))['total'] or 0

    received_pos = all_pos.filter(status='Received')
    received_count = received_pos.count()
    received_amount = received_pos.aggregate(total=Sum('total_amount'))['total'] or 0

    paid_pos = all_pos.filter(payment_status='Paid')
    paid_count = paid_pos.count()
    paid_amount = paid_pos.aggregate(total=Sum('total_amount'))['total'] or 0

    stats = {
        'total_count': total_count,
        'total_amount': total_amount,
        'open_count': open_count,
        'open_amount': open_amount,
        'received_count': received_count,
        'received_amount': received_amount,
        'paid_count': paid_count,
        'paid_amount': paid_amount,
    }

    suppliers = Supplier.objects.filter(status='Active').order_by('name')
    status_choices = PurchaseOrder.STATUS_CHOICES
    payment_choices = PurchaseOrder.PAYMENT_STATUS_CHOICES

    paginator = Paginator(pos.order_by('-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/procurement/orders.html', {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'payment': payment,
        'supplier_id': supplier_id,
        'stats': stats,
        'suppliers': suppliers,
        'status_choices': status_choices,
        'payment_choices': payment_choices,
        'active_nav': 'procurement',
    })


@login_required
def purchase_order_create(request):
    """Generate a formal Purchase Order."""
    pr_id = request.GET.get('pr')
    initial_data = {'status': 'Ordered', 'payment_status': 'Unpaid'}

    if pr_id:
        try:
            pr = PurchaseRequest.objects.get(id=pr_id)
            initial_data['purchase_request'] = pr.id
            if pr.supplier:
                initial_data['supplier'] = pr.supplier.id
            initial_data['items_description'] = f"Item: {pr.item_name}\nQty: {pr.quantity}\nDetails: {pr.items_description}"
            initial_data['total_amount'] = pr.estimated_amount
        except PurchaseRequest.DoesNotExist:
            pass

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()

            if po.purchase_request:
                po.purchase_request.status = 'Ordered'
                po.purchase_request.save()

            AuditLog.log(
                user=request.user,
                action='Created',
                module='PurchaseOrder',
                record_id=str(po.pk),
                record_repr=f"PO #{po.order_number} ({po.supplier.name})",
                new_values={'order_number': po.order_number, 'total_amount': str(po.total_amount)},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Purchase Order #{po.order_number} generated for {po.supplier.name}.')
            return redirect('purchase_order_list')
        else:
            messages.error(request, 'Please resolve the highlighted errors.')
    else:
        form = PurchaseOrderForm(initial=initial_data)

    return render(request, 'welfare_app/procurement/order_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'procurement',
    })


@login_required
def purchase_order_update(request, pk):
    """Edit a Purchase Order."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        if form.is_valid():
            updated = form.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='PurchaseOrder',
                record_id=str(po.pk),
                record_repr=f"PO #{po.order_number}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Purchase Order #{po.order_number} updated.')
            return redirect('purchase_order_list')
        else:
            messages.error(request, 'Please correct the errors.')
    else:
        form = PurchaseOrderForm(instance=po)

    return render(request, 'welfare_app/procurement/order_form.html', {
        'form': form,
        'po': po,
        'is_edit': True,
        'active_nav': 'procurement',
    })


@login_required
def purchase_order_delete(request, pk):
    """Delete a Purchase Order."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        po_num = po.order_number
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='PurchaseOrder',
            record_id=str(po.pk),
            record_repr=f"PO #{po_num}",
            ip_address=getattr(request, 'client_ip', None)
        )
        po.delete()
        messages.success(request, f'Purchase Order #{po_num} deleted.')
    return redirect('purchase_order_list')


@login_required
def purchase_order_status(request, pk):
    """Quick update fulfillment delivery status or payment status on a PO."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_payment = request.POST.get('payment_status')

        if new_status:
            po.status = new_status
            if new_status == 'Received' and not po.actual_delivery:
                po.actual_delivery = timezone.now().date()
            if po.purchase_request and new_status == 'Received':
                po.purchase_request.status = 'Completed'
                po.purchase_request.save()

        if new_payment:
            po.payment_status = new_payment

        po.save()

        AuditLog.log(
            user=request.user,
            action='Status Updated',
            module='PurchaseOrder',
            record_id=str(po.pk),
            record_repr=f"PO #{po.order_number} -> {po.status} / {po.payment_status}",
            ip_address=getattr(request, 'client_ip', None)
        )
        messages.success(request, f'Purchase Order #{po.order_number} status updated.')
    return redirect('purchase_order_list')

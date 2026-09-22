import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone

from ..models import Bill, BillDocument, Hospital, Employee, AuditLog
from ..forms.bill_forms import BillForm


def save_bill_attachments(bill, request):
    """Save or update dynamic documentation attachments and voucher remarks."""
    row_indices = request.POST.getlist('bill_doc_index')
    if not row_indices:
        return

    retained_ids = []
    for idx in row_indices:
        description = request.POST.get(f'bill_doc_remark_{idx}', '').strip()
        doc_file = request.FILES.get(f'bill_doc_file_{idx}')
        existing_id = request.POST.get(f'bill_doc_existing_id_{idx}')

        # If completely empty with no existing record, skip
        if not description and not doc_file and not existing_id:
            continue

        if existing_id:
            item = BillDocument.objects.filter(pk=existing_id, bill=bill).first()
            if item:
                item.description = description
                if doc_file:
                    item.document = doc_file
                item.save()
                retained_ids.append(item.pk)
        else:
            item = BillDocument.objects.create(
                bill=bill,
                description=description,
                document=doc_file
            )
            retained_ids.append(item.pk)

    # Delete any existing attachments that were removed by the user
    bill.attachments.exclude(pk__in=retained_ids).delete()



@login_required
def bill_list(request):
    """List, search, filter, and summarize bills and medical expenses."""
    bills = Bill.objects.select_related('hospital', 'employee', 'approved_by', 'created_by').prefetch_related('attachments').all()
    
    # URL Query Parameters
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    hospital_id = request.GET.get('hospital', '').strip()
    status = request.GET.get('status', '').strip()
    payment = request.GET.get('payment', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    # Search
    if q:
        bills = bills.filter(
            Q(bill_number__icontains=q) |
            Q(vendor_name__icontains=q) |
            Q(description__icontains=q) |
            Q(employee__name__icontains=q) |
            Q(employee__pl_number__icontains=q) |
            Q(hospital__name__icontains=q)
        )

    # Filters
    if category:
        bills = bills.filter(category=category)
    if hospital_id:
        bills = bills.filter(hospital_id=hospital_id)
    if status:
        bills = bills.filter(status=status)
    if payment:
        bills = bills.filter(payment_status=payment)
    if date_from:
        bills = bills.filter(bill_date__gte=date_from)
    if date_to:
        bills = bills.filter(bill_date__lte=date_to)

    # KPI Summary Statistics across all records
    all_bills = Bill.objects.all()
    total_count = all_bills.count()
    total_amount = all_bills.aggregate(total=Sum('amount'))['total'] or 0
    
    pending_bills = all_bills.filter(status='Pending')
    pending_count = pending_bills.count()
    pending_amount = pending_bills.aggregate(total=Sum('amount'))['total'] or 0
    
    approved_unpaid = all_bills.filter(status='Approved', payment_status__in=['Unpaid', 'Partially Paid'])
    approved_unpaid_count = approved_unpaid.count()
    approved_unpaid_amount = approved_unpaid.aggregate(total=Sum('amount'))['total'] or 0
    
    paid_bills = all_bills.filter(payment_status='Paid')
    paid_count = paid_bills.count()
    paid_amount = paid_bills.aggregate(total=Sum('amount'))['total'] or 0
    
    hospital_bills_amount = all_bills.filter(category='Hospital Bill').aggregate(total=Sum('amount'))['total'] or 0
    
    now = timezone.now()
    this_month_amount = all_bills.filter(bill_date__year=now.year, bill_date__month=now.month).aggregate(total=Sum('amount'))['total'] or 0

    stats = {
        'total_count': total_count,
        'total_amount': total_amount,
        'pending_count': pending_count,
        'pending_amount': pending_amount,
        'approved_unpaid_count': approved_unpaid_count,
        'approved_unpaid_amount': approved_unpaid_amount,
        'paid_count': paid_count,
        'paid_amount': paid_amount,
        'hospital_bills_amount': hospital_bills_amount,
        'this_month_amount': this_month_amount,
    }

    # Filter dropdown data
    hospitals = Hospital.objects.filter(status='Active').order_by('name')
    categories = Bill.CATEGORY_CHOICES
    status_choices = Bill.STATUS_CHOICES
    payment_choices = Bill.PAYMENT_STATUS_CHOICES

    # Pagination
    paginator = Paginator(bills.order_by('-bill_date', '-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/bills/list.html', {
        'page_obj': page_obj,
        'stats': stats,
        'hospitals': hospitals,
        'categories': categories,
        'status_choices': status_choices,
        'payment_choices': payment_choices,
        'q': q,
        'category': category,
        'hospital_id': hospital_id,
        'status': status,
        'payment': payment,
        'date_from': date_from,
        'date_to': date_to,
        'active_nav': 'bills_expenses',
    })


@login_required
def bill_create(request):
    """Create a new Bill or Direct Medical Expense."""
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.created_by = request.user
            if bill.status == 'Approved' and not bill.approved_by:
                bill.approved_by = request.user
            bill.save()
            save_bill_attachments(bill, request)

            AuditLog.log(
                user=request.user,
                action='Created',
                module='Bill',
                record_id=str(bill.pk),
                record_repr=f"Bill #{bill.bill_number} - Rs. {bill.amount:,.0f}",
                new_values={'bill_number': bill.bill_number, 'amount': str(bill.amount), 'category': bill.category},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Bill invoice #{bill.bill_number} recorded successfully.')
            return redirect('bill_list')
        else:
            messages.error(request, 'Please correct the highlighted errors in the form.')
    else:
        form = BillForm(initial={'bill_date': timezone.now().date(), 'payment_status': 'Unpaid', 'status': 'Pending'})

    return render(request, 'welfare_app/bills/form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'bills_expenses',
    })


@login_required
def bill_update(request, pk):
    """Edit an existing Bill or Medical Expense."""
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, instance=bill)
        if form.is_valid():
            updated_bill = form.save(commit=False)
            if updated_bill.status == 'Approved' and not updated_bill.approved_by:
                updated_bill.approved_by = request.user
            updated_bill.save()
            save_bill_attachments(updated_bill, request)

            AuditLog.log(
                user=request.user,
                action='Updated',
                module='Bill',
                record_id=str(bill.pk),
                record_repr=f"Bill #{bill.bill_number}",
                new_values={'status': updated_bill.status, 'payment_status': updated_bill.payment_status, 'amount': str(updated_bill.amount)},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Bill #{bill.bill_number} updated successfully.')
            return redirect('bill_list')
        else:
            messages.error(request, 'Please review and resolve the errors below.')
    else:
        form = BillForm(instance=bill)

    existing_attachments = [
        {
            'id': att.pk,
            'description': att.description or '',
            'doc_url': att.document.url if att.document else '',
            'doc_name': att.document.name.split('/')[-1] if att.document else '',
        }
        for att in bill.attachments.all()
    ]

    return render(request, 'welfare_app/bills/form.html', {
        'form': form,
        'bill': bill,
        'is_edit': True,
        'existing_attachments': existing_attachments,
        'active_nav': 'bills_expenses',
    })



@login_required
def bill_delete(request, pk):
    """Delete a Bill record."""
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        bill_num = bill.bill_number
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='Bill',
            record_id=str(bill.pk),
            record_repr=f"Bill #{bill_num}",
            ip_address=getattr(request, 'client_ip', None)
        )
        bill.delete()
        messages.success(request, f'Bill #{bill_num} was permanently removed.')
    return redirect('bill_list')


@login_required
def bill_approve(request, pk):
    """Perform quick approval, rejection, or mark-as-paid action on a Bill."""
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'approve').lower()
        if action == 'approve':
            bill.status = 'Approved'
            bill.approved_by = request.user
            messages.success(request, f'Bill #{bill.bill_number} has been approved.')
        elif action == 'reject':
            bill.status = 'Rejected'
            messages.warning(request, f'Bill #{bill.bill_number} marked as Rejected.')
        elif action == 'pay':
            bill.payment_status = 'Paid'
            bill.paid_date = timezone.now().date()
            messages.success(request, f'Bill #{bill.bill_number} marked as Paid.')
        elif action == 'unpay':
            bill.payment_status = 'Unpaid'
            bill.paid_date = None
            messages.info(request, f'Bill #{bill.bill_number} reset to Unpaid.')
        
        bill.save()

        AuditLog.log(
            user=request.user,
            action=action.title(),
            module='Bill',
            record_id=str(bill.pk),
            record_repr=f"Bill #{bill.bill_number} -> {action}",
            ip_address=getattr(request, 'client_ip', None)
        )
    return redirect('bill_list')

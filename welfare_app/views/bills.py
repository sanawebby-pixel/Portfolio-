from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import Bill, AuditLog
from ..forms.bill_forms import BillForm


@login_required
def bill_list(request):
    bills = Bill.objects.select_related('hospital', 'employee').all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    payment = request.GET.get('payment', '')
    
    if q:
        bills = bills.filter(
            Q(bill_number__icontains=q) | Q(vendor_name__icontains=q) |
            Q(employee__name__icontains=q)
        )
    if status:
        bills = bills.filter(status=status)
    if payment:
        bills = bills.filter(payment_status=payment)
    
    paginator = Paginator(bills.order_by('-bill_date'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'welfare_app/bills/list.html', {
        'page_obj': page_obj, 'q': q, 'status': status, 'payment': payment,
        'active_nav': 'bills_expenses',
    })


@login_required
def bill_create(request):
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.created_by = request.user
            bill.save()
            messages.success(request, f'Bill {bill.bill_number} created.')
            return redirect('bill_list')
    else:
        form = BillForm()
    return render(request, 'welfare_app/bills/form.html', {'form': form, 'active_nav': 'bills_expenses'})


@login_required
def bill_update(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, instance=bill)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bill {bill.bill_number} updated.')
            return redirect('bill_list')
    else:
        form = BillForm(instance=bill)
    return render(request, 'welfare_app/bills/form.html', {'form': form, 'bill': bill, 'active_nav': 'bills_expenses'})


@login_required
def bill_delete(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        bill.delete()
        messages.success(request, 'Bill deleted.')
    return redirect('bill_list')


@login_required
def bill_approve(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'approve')
        if action == 'approve':
            bill.status = 'Approved'
        elif action == 'reject':
            bill.status = 'Rejected'
        elif action == 'pay':
            bill.payment_status = 'Paid'
        bill.save()
        AuditLog.log(user=request.user, action=action.title(), module='Bill',
                    record_id=str(bill.pk), record_repr=f'Bill {bill.bill_number}',
                    ip_address=getattr(request, 'client_ip', None))
        messages.success(request, f'Bill {bill.bill_number} {action}d.')
    return redirect('bill_list')

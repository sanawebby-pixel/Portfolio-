from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from ..models import MedicalClaim, ClaimExpenseItem, ClaimPayment, ApprovalWorkflow, Employee, Hospital, Doctor, FinanceTransaction, AuditLog
from ..forms.claim_forms import MedicalClaimForm, ClaimPaymentForm, ClaimApprovalForm, ClaimExpenseItemFormSet


@login_required
def claim_list(request):
    claims = MedicalClaim.objects.select_related('employee', 'hospital', 'doctor', 'dependent').all()
    q = request.GET.get('q', '').strip()
    claim_status = request.GET.get('status', '').strip()
    payment_status = request.GET.get('payment', '').strip()
    hospital_id = request.GET.get('hospital', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    if q:
        claims = claims.filter(
            Q(claim_number__icontains=q) |
            Q(employee__name__icontains=q) |
            Q(employee__pl_number__icontains=q) |
            Q(bill_number__icontains=q) |
            Q(diagnosis__icontains=q)
        )
    if claim_status:
        claims = claims.filter(claim_status=claim_status)
    if payment_status:
        claims = claims.filter(payment_status=payment_status)
    if hospital_id:
        claims = claims.filter(hospital_id=hospital_id)
    if start_date:
        claims = claims.filter(claim_date__gte=start_date)
    if end_date:
        claims = claims.filter(claim_date__lte=end_date)
    
    # Aggregates for summary stats bar
    all_claims = MedicalClaim.objects.all()
    stats = {
        'total_count': all_claims.count(),
        'total_amount': all_claims.aggregate(s=Sum('total_bill_amount'))['s'] or 0,
        'pending_count': all_claims.filter(claim_status__in=['Pending', 'New', 'Under Review']).count(),
        'pending_amount': all_claims.filter(claim_status__in=['Pending', 'New', 'Under Review']).aggregate(s=Sum('total_bill_amount'))['s'] or 0,
        'approved_count': all_claims.filter(claim_status__in=['Approved', 'Partially Approved']).count(),
        'approved_amount': all_claims.filter(claim_status__in=['Approved', 'Partially Approved']).aggregate(s=Sum('approved_amount'))['s'] or 0,
        'paid_amount': all_claims.aggregate(s=Sum('paid_amount'))['s'] or 0,
        'rejected_count': all_claims.filter(claim_status='Rejected').count(),
    }
    
    hospitals = Hospital.objects.filter(status='Active').order_by('name')
    paginator = Paginator(claims.order_by('-claim_date', '-id'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'hospitals': hospitals,
        'q': q,
        'claim_status': claim_status,
        'payment_status': payment_status,
        'hospital_id': hospital_id,
        'start_date': start_date,
        'end_date': end_date,
        'active_nav': 'claims',
    }
    return render(request, 'welfare_app/claims/list.html', context)


@login_required
def claim_detail(request, pk):
    claim = get_object_or_404(
        MedicalClaim.objects.select_related('employee', 'hospital', 'doctor', 'dependent', 'created_by'),
        pk=pk
    )
    expense_items = ClaimExpenseItem.objects.filter(claim=claim)
    approvals = ApprovalWorkflow.objects.filter(claim=claim).select_related('approver').order_by('action_date')
    payments = ClaimPayment.objects.filter(claim=claim).select_related('paid_by').order_by('-payment_date')
    
    approval_form = ClaimApprovalForm()
    payment_form = ClaimPaymentForm(initial={'payment_amount': claim.remaining_payable_amount})
    
    context = {
        'claim': claim,
        'expense_items': expense_items,
        'approvals': approvals,
        'payments': payments,
        'approval_form': approval_form,
        'payment_form': payment_form,
        'active_nav': 'claims',
    }
    return render(request, 'welfare_app/claims/detail.html', context)


from decimal import Decimal


def save_claim_expense_items(claim, request):
    """Save dynamic itemized expense rows submitted from the claim form."""
    titles = request.POST.getlist('expense_item_title')
    costs = request.POST.getlist('expense_item_cost')
    if not titles:
        titles = request.POST.getlist('expense_item_title[]')
    if not costs:
        costs = request.POST.getlist('expense_item_cost[]')

    if titles is not None and costs is not None and len(titles) > 0:
        ClaimExpenseItem.objects.filter(claim=claim).delete()
        total_sum = Decimal('0.00')
        has_items = False

        for title, cost_str in zip(titles, costs):
            title = (title or '').strip()
            cost_str = (cost_str or '').strip()
            if not title and not cost_str:
                continue
            try:
                cost = Decimal(cost_str) if cost_str else Decimal('0.00')
            except Exception:
                cost = Decimal('0.00')

            ClaimExpenseItem.objects.create(
                claim=claim,
                category=title or 'Medical Expense',
                description=title or 'Medical Expense',
                amount=cost,
                eligible_amount=cost,
                approved_amount=cost
            )
            total_sum += cost
            has_items = True

        if has_items:
            claim.total_bill_amount = total_sum
            emp_co = claim.employee_contribution or Decimal('0.00')
            claim.claimable_amount = max(Decimal('0.00'), total_sum - emp_co)
            claim.welfare_contribution = claim.claimable_amount
            claim.save()


@login_required
def claim_create(request):
    existing_expenses = []
    if request.method == 'POST':
        form = MedicalClaimForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.created_by = request.user
            # Ensure safe default status
            if not claim.claim_status:
                claim.claim_status = 'Pending'
            if not claim.payment_status:
                claim.payment_status = 'Unpaid'
            claim.save()
            save_claim_expense_items(claim, request)
            
            # Record initial submission approval step
            ApprovalWorkflow.objects.create(
                claim=claim,
                stage='Submitted',
                approver=request.user,
                status='Pending',
                remarks='Claim registered into ERP system'
            )
            
            AuditLog.log(
                user=request.user,
                action='Created',
                module='MedicalClaim',
                record_id=str(claim.pk),
                record_repr=f'Claim {claim.claim_number} for {claim.employee.name} (Rs. {claim.total_bill_amount:,.0f})',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Medical Claim {claim.claim_number} successfully registered with status "{claim.claim_status}".')
            return redirect('claim_detail', pk=claim.pk)
        else:
            titles = request.POST.getlist('expense_item_title') or request.POST.getlist('expense_item_title[]')
            costs = request.POST.getlist('expense_item_cost') or request.POST.getlist('expense_item_cost[]')
            existing_expenses = [{'category': t, 'amount': c} for t, c in zip(titles, costs) if t or c]
    else:
        initial_data = {
            'claim_date': timezone.now().date(),
            'treatment_date': timezone.now().date(),
            'claim_status': 'Pending',
            'payment_status': 'Unpaid',
        }
        # Pre-select employee if passed in query param
        emp_id = request.GET.get('employee')
        if emp_id:
            initial_data['employee'] = emp_id
        form = MedicalClaimForm(initial=initial_data)
    
    return render(request, 'welfare_app/claims/form.html', {
        'form': form,
        'title': 'New Medical Claim Entry',
        'existing_expenses': existing_expenses,
        'active_nav': 'claims'
    })


@login_required
def claim_update(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if request.method == 'POST':
        form = MedicalClaimForm(request.POST, request.FILES, instance=claim)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.updated_by = request.user
            if not claim.payment_status:
                claim.payment_status = 'Unpaid'
            claim.save()
            save_claim_expense_items(claim, request)
            
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='MedicalClaim',
                record_id=str(claim.pk),
                record_repr=f'Updated Claim {claim.claim_number}',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Claim {claim.claim_number} has been updated.')
            return redirect('claim_detail', pk=claim.pk)
        else:
            titles = request.POST.getlist('expense_item_title') or request.POST.getlist('expense_item_title[]')
            costs = request.POST.getlist('expense_item_cost') or request.POST.getlist('expense_item_cost[]')
            existing_expenses = [{'category': t, 'amount': c} for t, c in zip(titles, costs) if t or c]
    else:
        form = MedicalClaimForm(instance=claim)
        existing_expenses = ClaimExpenseItem.objects.filter(claim=claim).order_by('id')
    
    return render(request, 'welfare_app/claims/form.html', {
        'form': form,
        'claim': claim,
        'existing_expenses': existing_expenses,
        'title': f'Edit Medical Claim ({claim.claim_number})',
        'active_nav': 'claims'
    })


@login_required
def claim_submit(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if claim.claim_status in ['Draft', 'New']:
        claim.claim_status = 'Pending'
        claim.save()
        ApprovalWorkflow.objects.create(
            claim=claim, stage='Welfare Review', approver=request.user,
            status='Pending', remarks='Claim submitted for Welfare Committee Review'
        )
        AuditLog.log(user=request.user, action='Submitted', module='MedicalClaim',
                    record_id=str(claim.pk), record_repr=f'Claim {claim.claim_number} submitted',
                    ip_address=getattr(request, 'client_ip', None))
        messages.success(request, f'Claim {claim.claim_number} submitted for welfare review.')
    return redirect('claim_detail', pk=pk)


@login_required
def claim_approve(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'Approved')
        remarks = request.POST.get('remarks', '').strip()
        approved_amount_str = request.POST.get('approved_amount', '').strip()
        
        if action in ['Approved', 'Partially Approved']:
            if approved_amount_str:
                try:
                    app_amount = float(approved_amount_str)
                except (ValueError, TypeError):
                    app_amount = float(claim.claimable_amount or claim.total_bill_amount)
            else:
                app_amount = float(claim.claimable_amount or claim.total_bill_amount)
            
            claim.approved_amount = app_amount
            if app_amount < float(claim.total_bill_amount):
                claim.claim_status = 'Partially Approved'
                claim.rejected_amount = float(claim.total_bill_amount) - app_amount
            else:
                claim.claim_status = 'Approved'
                claim.rejected_amount = 0
            
            # Payment status remains Unpaid until an actual payment is disbursed
            if claim.paid_amount >= claim.approved_amount and claim.approved_amount > 0:
                claim.payment_status = 'Paid'
            elif claim.paid_amount > 0:
                claim.payment_status = 'Partially Paid'
            else:
                claim.payment_status = 'Unpaid'
            
            claim.save()
            ApprovalWorkflow.objects.create(
                claim=claim,
                stage='Manager Approval',
                approver=request.user,
                status='Approved',
                approved_amount=claim.approved_amount,
                remarks=remarks or f'Approved for Rs. {claim.approved_amount:,.2f}'
            )
            AuditLog.log(user=request.user, action='Approved', module='MedicalClaim',
                        record_id=str(claim.pk),
                        record_repr=f'Claim {claim.claim_number} approved for Rs. {claim.approved_amount:,.2f}',
                        ip_address=getattr(request, 'client_ip', None))
            messages.success(request, f'Claim {claim.claim_number} approved for Rs. {claim.approved_amount:,.2f}. Ready for payment disbursement.')
        
        elif action == 'Rejected':
            if not remarks:
                messages.error(request, 'A detailed rejection reason is required to reject a claim.')
                return redirect('claim_detail', pk=pk)
            
            claim.claim_status = 'Rejected'
            claim.rejected_amount = claim.total_bill_amount
            claim.approved_amount = 0
            claim.rejection_reason = remarks
            claim.save()
            
            ApprovalWorkflow.objects.create(
                claim=claim,
                stage='Rejected',
                approver=request.user,
                status='Rejected',
                remarks=remarks
            )
            AuditLog.log(user=request.user, action='Rejected', module='MedicalClaim',
                        record_id=str(claim.pk),
                        record_repr=f'Claim {claim.claim_number} rejected. Reason: {remarks}',
                        ip_address=getattr(request, 'client_ip', None))
            messages.warning(request, f'Claim {claim.claim_number} has been rejected.')
        
        elif action == 'Returned':
            claim.claim_status = 'Under Review'
            claim.save()
            ApprovalWorkflow.objects.create(
                claim=claim,
                stage='Returned',
                approver=request.user,
                status='Returned',
                remarks=remarks or 'Returned for documentation correction'
            )
            messages.info(request, f'Claim {claim.claim_number} returned for review.')
            
    return redirect('claim_detail', pk=pk)


@login_required
def claim_reject(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '').strip()
        if not remarks:
            messages.error(request, 'Rejection reason is required.')
            return redirect('claim_detail', pk=pk)
        
        claim.claim_status = 'Rejected'
        claim.rejected_amount = claim.total_bill_amount
        claim.approved_amount = 0
        claim.rejection_reason = remarks
        claim.save()
        
        ApprovalWorkflow.objects.create(
            claim=claim,
            stage='Rejected',
            approver=request.user,
            status='Rejected',
            remarks=remarks
        )
        AuditLog.log(user=request.user, action='Rejected', module='MedicalClaim',
                    record_id=str(claim.pk), record_repr=f'Claim {claim.claim_number} rejected: {remarks}',
                    ip_address=getattr(request, 'client_ip', None))
        messages.warning(request, f'Claim {claim.claim_number} rejected.')
    return redirect('claim_detail', pk=pk)


@login_required
def claim_payment_create(request, pk):
    """Record a disbursement payment against an approved claim."""
    claim = get_object_or_404(MedicalClaim, pk=pk)
    
    if claim.claim_status not in ['Approved', 'Partially Approved', 'Paid']:
        messages.error(request, 'Payments can only be disbursed against approved claims.')
        return redirect('claim_detail', pk=pk)
    
    if request.method == 'POST':
        form = ClaimPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.claim = claim
            payment.employee = claim.employee
            payment.approved_amount = claim.approved_amount
            payment.paid_by = request.user
            payment.save()
            
            # Create corresponding Treasury transaction
            FinanceTransaction.objects.create(
                transaction_type='Payment',
                amount=payment.payment_amount,
                category='Medical Claim Disbursement',
                description=f'Disbursement for Claim {claim.claim_number} ({claim.employee.name}) - {payment.payment_method}',
                reference_number=payment.payment_number,
                payment_method=payment.payment_method,
                account=payment.account or 'Welfare Main Account (HBL)',
                related_claim=claim,
                date=payment.payment_date,
                created_by=request.user,
                attachment=payment.receipt_attachment if payment.receipt_attachment else None,
            )
            
            # Record approval workflow step
            ApprovalWorkflow.objects.create(
                claim=claim,
                stage='Payment',
                approver=request.user,
                status='Approved',
                approved_amount=payment.payment_amount,
                remarks=f'Disbursed Rs. {payment.payment_amount:,.2f} via {payment.payment_method} (Ref: {payment.transaction_reference or payment.payment_number})'
            )
            
            AuditLog.log(
                user=request.user,
                action='Paid',
                module='ClaimPayment',
                record_id=str(payment.pk),
                record_repr=f'Payment of Rs. {payment.payment_amount:,.2f} disbursed for Claim {claim.claim_number}',
                ip_address=getattr(request, 'client_ip', None)
            )
            
            messages.success(request, f'Payment of Rs. {payment.payment_amount:,.2f} successfully recorded. Payment Receipt #{payment.payment_number} generated.')
            return redirect('claim_detail', pk=pk)
        else:
            messages.error(request, 'Failed to record payment. Please check the entered data.')
    
    return redirect('claim_detail', pk=pk)


@login_required
def claim_print(request, pk):
    """Printable official voucher for a medical claim."""
    claim = get_object_or_404(
        MedicalClaim.objects.select_related('employee', 'hospital', 'doctor', 'dependent', 'created_by'),
        pk=pk
    )
    expense_items = ClaimExpenseItem.objects.filter(claim=claim)
    approvals = ApprovalWorkflow.objects.filter(claim=claim).select_related('approver').order_by('action_date')
    payments = ClaimPayment.objects.filter(claim=claim).select_related('paid_by')
    
    return render(request, 'welfare_app/claims/print_voucher.html', {
        'claim': claim,
        'expense_items': expense_items,
        'approvals': approvals,
        'payments': payments,
        'today': timezone.now().date(),
    })


@login_required
def claim_delete(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if claim.claim_status in ['Draft', 'New', 'Pending']:
        c_num = claim.claim_number
        claim.delete()
        AuditLog.log(user=request.user, action='Deleted', module='MedicalClaim',
                    record_id=str(pk), record_repr=f'Deleted Claim {c_num}',
                    ip_address=getattr(request, 'client_ip', None))
        messages.success(request, f'Claim {c_num} was deleted.')
        return redirect('claim_list')
    messages.error(request, 'Cannot delete an approved, rejected, or processed claim.')
    return redirect('claim_detail', pk=pk)

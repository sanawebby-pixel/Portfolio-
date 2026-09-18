from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from ..models import MedicalClaim, ClaimExpenseItem, ApprovalWorkflow, Employee, Hospital, AuditLog
from ..forms.claim_forms import MedicalClaimForm, ClaimExpenseItemFormSet


@login_required
def claim_list(request):
    claims = MedicalClaim.objects.select_related('employee', 'hospital').all()
    q = request.GET.get('q', '')
    claim_status = request.GET.get('status', '')
    payment_status = request.GET.get('payment', '')
    
    if q:
        claims = claims.filter(
            Q(claim_number__icontains=q) | Q(employee__name__icontains=q) |
            Q(employee__pl_number__icontains=q)
        )
    if claim_status:
        claims = claims.filter(claim_status=claim_status)
    if payment_status:
        claims = claims.filter(payment_status=payment_status)
    
    paginator = Paginator(claims.order_by('-claim_date'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'claim_status': claim_status,
        'payment_status': payment_status,
        'active_nav': 'claims',
    }
    return render(request, 'welfare_app/claims/list.html', context)


@login_required
def claim_detail(request, pk):
    claim = get_object_or_404(
        MedicalClaim.objects.select_related('employee', 'hospital', 'doctor', 'dependent'),
        pk=pk
    )
    expense_items = ClaimExpenseItem.objects.filter(claim=claim)
    approvals = ApprovalWorkflow.objects.filter(claim=claim).select_related('approver').order_by('action_date')
    
    # Calculate totals from line items
    totals = expense_items.aggregate(
        total_amount=Sum('amount'),
        total_eligible=Sum('eligible_amount'),
        total_approved=Sum('approved_amount'),
    )
    
    context = {
        'claim': claim,
        'expense_items': expense_items,
        'approvals': approvals,
        'totals': totals,
        'active_nav': 'claims',
    }
    return render(request, 'welfare_app/claims/detail.html', context)


@login_required
def claim_create(request):
    if request.method == 'POST':
        form = MedicalClaimForm(request.POST)
        formset = ClaimExpenseItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            claim = form.save(commit=False)
            claim.created_by = request.user
            claim.save()
            formset.instance = claim
            formset.save()
            # Recalculate totals from items
            total = claim.expense_items.aggregate(total=Sum('amount'))['total'] or 0
            eligible = claim.expense_items.aggregate(total=Sum('eligible_amount'))['total'] or 0
            claim.total_bill_amount = total
            claim.eligible_amount = eligible
            claim.save()
            AuditLog.log(user=request.user, action='Created', module='MedicalClaim',
                        record_id=str(claim.pk), record_repr=f'Claim {claim.claim_number}',
                        ip_address=getattr(request, 'client_ip', None))
            messages.success(request, f'Claim {claim.claim_number} created.')
            return redirect('claim_detail', pk=claim.pk)
    else:
        form = MedicalClaimForm()
        formset = ClaimExpenseItemFormSet(prefix='items')
    
    return render(request, 'welfare_app/claims/form.html', {
        'form': form, 'formset': formset, 'active_nav': 'claims'
    })


@login_required
def claim_update(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if request.method == 'POST':
        form = MedicalClaimForm(request.POST, instance=claim)
        formset = ClaimExpenseItemFormSet(request.POST, instance=claim, prefix='items')
        if form.is_valid() and formset.is_valid():
            claim = form.save(commit=False)
            claim.updated_by = request.user
            claim.save()
            formset.save()
            # Recalculate totals
            total = claim.expense_items.aggregate(total=Sum('amount'))['total'] or 0
            eligible = claim.expense_items.aggregate(total=Sum('eligible_amount'))['total'] or 0
            claim.total_bill_amount = total
            claim.eligible_amount = eligible
            claim.save()
            messages.success(request, f'Claim {claim.claim_number} updated.')
            return redirect('claim_detail', pk=claim.pk)
    else:
        form = MedicalClaimForm(instance=claim)
        formset = ClaimExpenseItemFormSet(instance=claim, prefix='items')
    
    return render(request, 'welfare_app/claims/form.html', {
        'form': form, 'formset': formset, 'claim': claim, 'active_nav': 'claims'
    })


@login_required
def claim_submit(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if claim.claim_status == 'Draft':
        claim.claim_status = 'Submitted'
        claim.save()
        ApprovalWorkflow.objects.create(
            claim=claim, stage='Submitted', approver=request.user,
            status='Approved', remarks='Claim submitted for review'
        )
        AuditLog.log(user=request.user, action='Submitted', module='MedicalClaim',
                    record_id=str(claim.pk), record_repr=f'Claim {claim.claim_number}',
                    ip_address=getattr(request, 'client_ip', None))
        messages.success(request, f'Claim {claim.claim_number} submitted for review.')
    return redirect('claim_detail', pk=pk)


@login_required
def claim_approve(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    remarks = request.POST.get('remarks', '')
    approved_amount = request.POST.get('approved_amount', '')
    
    if claim.claim_status in ['Submitted', 'Under Review']:
        # Determine next stage
        current_approvals = claim.approvals.count()
        if current_approvals <= 1:
            stage = 'Welfare Review'
            claim.claim_status = 'Under Review'
        elif current_approvals == 2:
            stage = 'Manager Approval'
            claim.claim_status = 'Under Review'
        else:
            stage = 'Finance Verification'
            claim.claim_status = 'Approved'
            if approved_amount:
                try:
                    claim.approved_amount = float(approved_amount)
                except (ValueError, TypeError):
                    pass
        
        claim.save()
        ApprovalWorkflow.objects.create(
            claim=claim, stage=stage, approver=request.user,
            status='Approved', remarks=remarks or 'Approved'
        )
        AuditLog.log(user=request.user, action='Approved', module='MedicalClaim',
                    record_id=str(claim.pk), record_repr=f'Claim {claim.claim_number} - {stage}',
                    ip_address=getattr(request, 'client_ip', None))
        messages.success(request, f'Claim {claim.claim_number} approved at {stage}.')
    return redirect('claim_detail', pk=pk)


@login_required
def claim_reject(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    remarks = request.POST.get('remarks', 'Rejected')
    if claim.claim_status in ['Submitted', 'Under Review']:
        claim.claim_status = 'Rejected'
        claim.rejected_amount = claim.total_bill_amount
        claim.save()
        ApprovalWorkflow.objects.create(
            claim=claim, stage='Rejected', approver=request.user,
            status='Rejected', remarks=remarks
        )
        AuditLog.log(user=request.user, action='Rejected', module='MedicalClaim',
                    record_id=str(claim.pk), record_repr=f'Claim {claim.claim_number}',
                    ip_address=getattr(request, 'client_ip', None))
        messages.warning(request, f'Claim {claim.claim_number} rejected.')
    return redirect('claim_detail', pk=pk)


@login_required
def claim_delete(request, pk):
    claim = get_object_or_404(MedicalClaim, pk=pk)
    if claim.claim_status == 'Draft':
        claim.delete()
        messages.success(request, 'Draft claim deleted.')
        return redirect('claim_list')
    messages.error(request, 'Only draft claims can be deleted.')
    return redirect('claim_detail', pk=pk)

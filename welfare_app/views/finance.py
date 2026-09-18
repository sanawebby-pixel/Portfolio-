import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from django.utils import timezone

from ..models import Budget, FinanceTransaction, MedicalClaim, Bill, Department, AuditLog
from ..forms.finance_forms import BudgetForm, FinanceTransactionForm


@login_required
def finance_dashboard(request):
    """Executive Treasury & Financial Management Dashboard."""
    now = timezone.now()
    current_year = int(request.GET.get('year', now.year))

    # Budgets for the chosen fiscal year
    budgets = Budget.objects.filter(year=current_year).select_related('department')
    total_budget = budgets.filter(is_active=True).aggregate(total=Sum('allocated_amount'))['total'] or 0

    # Claims spending in the current fiscal year
    claims_qs = MedicalClaim.objects.filter(claim_date__year=current_year)
    approved_claims = claims_qs.filter(
        claim_status__in=['Approved', 'Partially Approved', 'Paid']
    ).aggregate(total=Sum('approved_amount'))['total'] or 0

    paid_claims = claims_qs.filter(
        payment_status='Paid'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    pending_claim_payments = claims_qs.filter(
        claim_status__in=['Approved', 'Partially Approved'],
        payment_status__in=['Unpaid', 'Partially Paid']
    ).aggregate(total=Sum('approved_amount'))['total'] or 0

    # Direct Medical & Vendor Bills in current fiscal year
    bills_qs = Bill.objects.filter(bill_date__year=current_year)
    total_bills = bills_qs.aggregate(total=Sum('amount'))['total'] or 0
    paid_bills = bills_qs.filter(payment_status='Paid').aggregate(total=Sum('amount'))['total'] or 0
    pending_bills = bills_qs.filter(payment_status__in=['Unpaid', 'Partially Paid']).aggregate(total=Sum('amount'))['total'] or 0

    # Treasury Inflows & Outflows from Finance Transactions
    tx_qs = FinanceTransaction.objects.filter(date__year=current_year)
    treasury_inflow = tx_qs.filter(transaction_type='Income').aggregate(total=Sum('amount'))['total'] or 0
    treasury_outflow = tx_qs.filter(transaction_type__in=['Expense', 'Payment']).aggregate(total=Sum('amount'))['total'] or 0
    treasury_refunds = tx_qs.filter(transaction_type='Refund').aggregate(total=Sum('amount'))['total'] or 0
    net_treasury_cash = (treasury_inflow + treasury_refunds) - treasury_outflow

    # Total welfare expenditure (Claims + Direct Bills)
    total_welfare_expense = approved_claims + total_bills
    remaining_budget = max(0, total_budget - total_welfare_expense)
    budget_utilization_pct = (total_welfare_expense / total_budget * 100) if total_budget > 0 else 0

    # Departmental Budgets Breakdown
    dept_budget_data = []
    for b in budgets:
        used = b.used_amount
        allocated = float(b.allocated_amount)
        rem = max(0.0, allocated - used)
        pct = min(100.0, (used / allocated * 100)) if allocated > 0 else 0
        dept_budget_data.append({
            'budget': b,
            'dept_name': b.department.name if b.department else 'Organization-wide Fund',
            'allocated': allocated,
            'used': used,
            'remaining': rem,
            'percentage': round(pct, 1),
            'status': 'Normal' if pct < 80 else ('Warning' if pct < 100 else 'Exceeded'),
        })

    # Monthly Cash Outflow Chart Data (12 Months)
    monthly_claims = []
    monthly_bills = []
    months_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for m in range(1, 13):
        m_claims = claims_qs.filter(claim_date__month=m, payment_status='Paid').aggregate(total=Sum('paid_amount'))['total'] or 0
        m_bills = bills_qs.filter(bill_date__month=m, payment_status='Paid').aggregate(total=Sum('amount'))['total'] or 0
        monthly_claims.append(float(m_claims))
        monthly_bills.append(float(m_bills))

    # Recent Transactions Ledger
    recent_transactions = FinanceTransaction.objects.select_related('related_claim', 'created_by').order_by('-date', '-created_at')[:8]

    # Available fiscal years
    available_years = Budget.objects.values_list('year', flat=True).distinct().order_by('-year')
    if not available_years:
        available_years = [now.year, now.year - 1]

    context = {
        'current_year': current_year,
        'available_years': available_years,
        'total_budget': total_budget,
        'approved_claims': approved_claims,
        'paid_claims': paid_claims,
        'pending_claim_payments': pending_claim_payments,
        'total_bills': total_bills,
        'paid_bills': paid_bills,
        'pending_bills': pending_bills,
        'treasury_inflow': treasury_inflow,
        'treasury_outflow': treasury_outflow,
        'net_treasury_cash': net_treasury_cash,
        'total_welfare_expense': total_welfare_expense,
        'remaining_budget': remaining_budget,
        'budget_utilization_pct': round(budget_utilization_pct, 1),
        'dept_budget_data': dept_budget_data,
        'months_labels_json': json.dumps(months_labels),
        'monthly_claims_json': json.dumps(monthly_claims),
        'monthly_bills_json': json.dumps(monthly_bills),
        'recent_transactions': recent_transactions,
        'active_nav': 'finance',
    }
    return render(request, 'welfare_app/finance/dashboard.html', context)


@login_required
def budget_list(request):
    """List departmental and welfare budget allocations."""
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    dept_id = request.GET.get('department', '').strip()
    category = request.GET.get('category', '').strip()

    budgets = Budget.objects.filter(year=year).select_related('department')

    if dept_id:
        budgets = budgets.filter(department_id=dept_id)
    if category:
        budgets = budgets.filter(category=category)

    # Calculate KPIs for the filtered year
    all_year_budgets = Budget.objects.filter(year=year)
    total_allocated = all_year_budgets.aggregate(total=Sum('allocated_amount'))['total'] or 0
    active_count = all_year_budgets.filter(is_active=True).count()

    total_used = sum(b.used_amount for b in all_year_budgets)
    total_remaining = max(0.0, float(total_allocated) - total_used)
    overall_pct = (total_used / float(total_allocated) * 100) if total_allocated > 0 else 0

    stats = {
        'total_allocated': total_allocated,
        'total_used': total_used,
        'total_remaining': total_remaining,
        'overall_pct': round(overall_pct, 1),
        'active_count': active_count,
    }

    # Available years & departments for filter
    available_years = Budget.objects.values_list('year', flat=True).distinct().order_by('-year')
    if not available_years:
        available_years = [now.year]
    departments = Department.objects.filter(is_active=True).order_by('name')
    categories = Budget.CATEGORY_CHOICES

    paginator = Paginator(budgets.order_by('department__name', 'category'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/finance/budgets.html', {
        'page_obj': page_obj,
        'year': year,
        'dept_id': dept_id,
        'category': category,
        'stats': stats,
        'available_years': available_years,
        'departments': departments,
        'categories': categories,
        'active_nav': 'budgets',
    })


@login_required
def budget_create(request):
    """Create a new Departmental / Welfare Budget."""
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save()
            AuditLog.log(
                user=request.user,
                action='Created',
                module='Budget',
                record_id=str(budget.pk),
                record_repr=str(budget),
                new_values={'year': budget.year, 'allocated_amount': str(budget.allocated_amount)},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Budget allocation for {budget.year} ({budget.category}) created successfully.')
            return redirect('budget_list')
        else:
            messages.error(request, 'Please resolve the highlighted errors below.')
    else:
        now = timezone.now()
        form = BudgetForm(initial={'year': now.year, 'category': 'Medical', 'is_active': True})

    return render(request, 'welfare_app/finance/budget_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'budgets',
    })


@login_required
def budget_update(request, pk):
    """Edit an existing Departmental / Welfare Budget."""
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            updated = form.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='Budget',
                record_id=str(budget.pk),
                record_repr=str(budget),
                new_values={'allocated_amount': str(updated.allocated_amount), 'is_active': updated.is_active},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Budget allocation {budget.year} updated.')
            return redirect('budget_list')
        else:
            messages.error(request, 'Please review and fix the errors.')
    else:
        form = BudgetForm(instance=budget)

    return render(request, 'welfare_app/finance/budget_form.html', {
        'form': form,
        'budget': budget,
        'is_edit': True,
        'active_nav': 'budgets',
    })


@login_required
def budget_delete(request, pk):
    """Delete a budget record."""
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        repr_str = str(budget)
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='Budget',
            record_id=str(budget.pk),
            record_repr=repr_str,
            ip_address=getattr(request, 'client_ip', None)
        )
        budget.delete()
        messages.success(request, f'Budget {repr_str} removed.')
    return redirect('budget_list')


@login_required
def transaction_list(request):
    """Treasury & Finance Transactions Ledger."""
    transactions = FinanceTransaction.objects.select_related('related_claim', 'created_by', 'approved_by').all()

    q = request.GET.get('q', '').strip()
    tx_type = request.GET.get('type', '').strip()
    method = request.GET.get('method', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if q:
        transactions = transactions.filter(
            Q(transaction_id__icontains=q) |
            Q(reference_number__icontains=q) |
            Q(category__icontains=q) |
            Q(account__icontains=q) |
            Q(description__icontains=q)
        )
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    if method:
        transactions = transactions.filter(payment_method=method)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    # KPI Summary Figures
    all_tx = FinanceTransaction.objects.all()
    total_inflow = all_tx.filter(transaction_type='Income').aggregate(total=Sum('amount'))['total'] or 0
    total_outflow = all_tx.filter(transaction_type__in=['Expense', 'Payment']).aggregate(total=Sum('amount'))['total'] or 0
    total_refund = all_tx.filter(transaction_type='Refund').aggregate(total=Sum('amount'))['total'] or 0
    net_liquidity = (total_inflow + total_refund) - total_outflow
    total_count = all_tx.count()

    stats = {
        'total_inflow': total_inflow,
        'total_outflow': total_outflow,
        'total_refund': total_refund,
        'net_liquidity': net_liquidity,
        'total_count': total_count,
    }

    types = FinanceTransaction.TYPE_CHOICES
    methods = FinanceTransaction.METHOD_CHOICES

    paginator = Paginator(transactions.order_by('-date', '-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/finance/transactions.html', {
        'page_obj': page_obj,
        'q': q,
        'tx_type': tx_type,
        'method': method,
        'date_from': date_from,
        'date_to': date_to,
        'stats': stats,
        'types': types,
        'methods': methods,
        'active_nav': 'finance',
    })


@login_required
def transaction_create(request):
    """Record a new Treasury Transaction / Cash Inflow / Outflow."""
    if request.method == 'POST':
        form = FinanceTransactionForm(request.POST, request.FILES)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.created_by = request.user
            if not tx.approved_by:
                tx.approved_by = request.user
            tx.save()

            AuditLog.log(
                user=request.user,
                action='Created',
                module='FinanceTransaction',
                record_id=str(tx.pk),
                record_repr=f"Tx #{tx.transaction_id} ({tx.transaction_type}: Rs. {tx.amount:,.0f})",
                new_values={'type': tx.transaction_type, 'amount': str(tx.amount)},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Treasury transaction #{tx.transaction_id} logged successfully.')
            return redirect('transaction_list')
        else:
            messages.error(request, 'Please correct the transaction errors below.')
    else:
        form = FinanceTransactionForm(initial={'date': timezone.now().date(), 'payment_method': 'Bank Transfer'})

    return render(request, 'welfare_app/finance/transaction_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'finance',
    })


@login_required
def transaction_delete(request, pk):
    """Delete a transaction record."""
    tx = get_object_or_404(FinanceTransaction, pk=pk)
    if request.method == 'POST':
        tx_repr = str(tx)
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='FinanceTransaction',
            record_id=str(tx.pk),
            record_repr=tx_repr,
            ip_address=getattr(request, 'client_ip', None)
        )
        tx.delete()
        messages.success(request, f'Transaction {tx_repr} deleted.')
    return redirect('transaction_list')

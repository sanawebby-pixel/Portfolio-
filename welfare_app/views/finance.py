from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from ..models import Budget, FinanceTransaction, MedicalClaim, Bill, AuditLog
from ..forms.finance_forms import BudgetForm, FinanceTransactionForm


@login_required
def finance_dashboard(request):
    now = timezone.now()
    current_year = now.year
    
    budgets = Budget.objects.filter(year=current_year, is_active=True)
    total_budget = budgets.aggregate(total=Sum('allocated_amount'))['total'] or 0
    
    approved_claims = MedicalClaim.objects.filter(
        claim_status__in=['Approved', 'Partially Approved', 'Paid']
    ).aggregate(total=Sum('approved_amount'))['total'] or 0
    
    pending_payments = MedicalClaim.objects.filter(
        payment_status__in=['Unpaid', 'Partially Paid'],
        claim_status__in=['Approved', 'Partially Approved']
    ).aggregate(total=Sum('approved_amount'))['total'] or 0
    
    paid_amount = MedicalClaim.objects.filter(
        payment_status='Paid'
    ).aggregate(total=Sum('approved_amount'))['total'] or 0
    
    recent_transactions = FinanceTransaction.objects.order_by('-date')[:10]
    
    context = {
        'total_budget': total_budget,
        'approved_claims': approved_claims,
        'pending_payments': pending_payments,
        'paid_amount': paid_amount,
        'remaining_budget': total_budget - approved_claims,
        'utilization': (approved_claims / total_budget * 100) if total_budget > 0 else 0,
        'recent_transactions': recent_transactions,
        'budgets': budgets,
        'current_year': current_year,
        'active_nav': 'finance',
    }
    return render(request, 'welfare_app/finance/dashboard.html', context)


@login_required
def budget_list(request):
    year = request.GET.get('year', timezone.now().year)
    budgets = Budget.objects.filter(year=year).select_related('department')
    paginator = Paginator(budgets.order_by('department__name'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'welfare_app/finance/budgets.html', {
        'page_obj': page_obj, 'year': year, 'active_nav': 'budgets',
    })


@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget created.')
            return redirect('budget_list')
    else:
        form = BudgetForm()
    return render(request, 'welfare_app/finance/budget_form.html', {'form': form, 'active_nav': 'budgets'})


@login_required
def budget_update(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated.')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)
    return render(request, 'welfare_app/finance/budget_form.html', {'form': form, 'budget': budget, 'active_nav': 'budgets'})


@login_required
def transaction_list(request):
    transactions = FinanceTransaction.objects.all()
    tx_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    paginator = Paginator(transactions.order_by('-date'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'welfare_app/finance/transactions.html', {
        'page_obj': page_obj, 'tx_type': tx_type, 'date_from': date_from, 'date_to': date_to,
        'active_nav': 'finance',
    })


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = FinanceTransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.created_by = request.user
            tx.save()
            messages.success(request, 'Transaction recorded.')
            return redirect('transaction_list')
    else:
        form = FinanceTransactionForm()
    return render(request, 'welfare_app/finance/transaction_form.html', {'form': form, 'active_nav': 'finance'})

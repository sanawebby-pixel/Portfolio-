from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.management import call_command
from django.db.models import Count, Q, Sum
from ..models import Department, BenefitRule, Employee, Budget, AuditLog
from ..forms.settings_forms import DepartmentForm, BenefitRuleForm


@login_required
def settings_index(request):
    """System Settings & Welfare Configuration Dashboard."""
    departments_count = Department.objects.count()
    active_departments = Department.objects.filter(is_active=True).count()
    benefit_rules_count = BenefitRule.objects.count()
    active_rules = BenefitRule.objects.filter(is_active=True).count()
    total_employees = Employee.objects.count()

    # System parameters summary
    system_config = {
        'currency': 'PKR (Rs.)',
        'fiscal_year': '2026',
        'erp_version': 'v2.4.0 Enterprise',
        'default_currency_symbol': 'Rs.',
        'audit_logging_enabled': True,
        'departments_count': departments_count,
        'active_departments': active_departments,
        'benefit_rules_count': benefit_rules_count,
        'active_rules': active_rules,
        'total_employees': total_employees,
    }

    # Recent benefit rules preview
    recent_rules = BenefitRule.objects.select_related('department').order_by('-created_at')[:5]

    return render(request, 'welfare_app/settings/index.html', {
        'config': system_config,
        'recent_rules': recent_rules,
        'active_nav': 'settings',
    })


# -------------------------------------------------------------
# Department CRUD
# -------------------------------------------------------------

@login_required
def department_list(request):
    """List all company & factory departments with employee counts and active status."""
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    departments = Department.objects.all().order_by('name')

    if q:
        departments = departments.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q))
    if status == 'active':
        departments = departments.filter(is_active=True)
    elif status == 'inactive':
        departments = departments.filter(is_active=False)

    dept_rows = []
    for d in departments:
        emp_count = Employee.objects.filter(department__iexact=d.name).count()
        budget_count = Budget.objects.filter(department=d).count()
        rule_count = BenefitRule.objects.filter(department=d).count()
        dept_rows.append({
            'department': d,
            'employee_count': emp_count,
            'budget_count': budget_count,
            'rule_count': rule_count,
        })

    paginator = Paginator(dept_rows, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/settings/departments.html', {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'total_count': len(dept_rows),
        'active_nav': 'settings',
    })


@login_required
def department_create(request):
    """Create a new factory department."""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            AuditLog.log(
                user=request.user,
                action='Created',
                module='Department',
                record_id=str(dept.pk),
                record_repr=f"Department: {dept.name} ({dept.code or 'No Code'})",
                new_values={'name': dept.name, 'code': dept.code, 'is_active': dept.is_active},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"Department '{dept.name}' was successfully created.")
            return redirect('department_list')
    else:
        form = DepartmentForm()

    return render(request, 'welfare_app/settings/department_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'settings',
    })


@login_required
def department_update(request, pk):
    """Update an existing department."""
    dept = get_object_or_404(Department, pk=pk)
    old_values = {'name': dept.name, 'code': dept.code, 'is_active': dept.is_active}

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            dept = form.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='Department',
                record_id=str(dept.pk),
                record_repr=f"Department: {dept.name}",
                old_values=old_values,
                new_values={'name': dept.name, 'code': dept.code, 'is_active': dept.is_active},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"Department '{dept.name}' details updated.")
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=dept)

    return render(request, 'welfare_app/settings/department_form.html', {
        'form': form,
        'department': dept,
        'is_edit': True,
        'active_nav': 'settings',
    })


@login_required
def department_delete(request, pk):
    """Delete or deactivate a department."""
    dept = get_object_or_404(Department, pk=pk)
    dept_name = dept.name

    # Check if department is associated with employees or budgets
    has_employees = Employee.objects.filter(department__iexact=dept.name).exists()
    has_budgets = Budget.objects.filter(department=dept).exists()

    if request.method == 'POST':
        if has_employees or has_budgets:
            # Soft deactivate if has records
            dept.is_active = False
            dept.save()
            messages.warning(request, f"Department '{dept_name}' has linked employee or budget records and has been deactivated instead of deleted.")
        else:
            dept.delete()
            AuditLog.log(
                user=request.user,
                action='Deleted',
                module='Department',
                record_id=str(pk),
                record_repr=f"Deleted Department: {dept_name}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"Department '{dept_name}' was successfully deleted.")
        return redirect('department_list')

    return render(request, 'welfare_app/components/confirm_delete.html', {
        'object_name': f"Department: {dept_name}",
        'cancel_url': 'department_list',
        'active_nav': 'settings',
    })


# -------------------------------------------------------------
# BenefitRule CRUD
# -------------------------------------------------------------

@login_required
def benefit_rule_list(request):
    """List all Welfare Benefit and Healthcare policy coverage rules."""
    q = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '').strip()
    status = request.GET.get('status', '').strip()

    rules = BenefitRule.objects.select_related('department').all().order_by('name')

    if q:
        rules = rules.filter(Q(name__icontains=q) | Q(grade_scale__icontains=q) | Q(description__icontains=q))
    if dept_id:
        rules = rules.filter(department_id=dept_id)
    if status == 'active':
        rules = rules.filter(is_active=True)
    elif status == 'inactive':
        rules = rules.filter(is_active=False)

    departments = Department.objects.filter(is_active=True).order_by('name')

    paginator = Paginator(rules, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/settings/benefit_rules.html', {
        'page_obj': page_obj,
        'q': q,
        'dept_id': dept_id,
        'status': status,
        'departments': departments,
        'active_nav': 'settings',
    })


@login_required
def benefit_rule_create(request):
    """Create a new welfare healthcare coverage policy rule."""
    if request.method == 'POST':
        form = BenefitRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            AuditLog.log(
                user=request.user,
                action='Created',
                module='BenefitRule',
                record_id=str(rule.pk),
                record_repr=f"Benefit Rule: {rule.name} (Limit Rs. {rule.annual_medical_limit:,.0f})",
                new_values={'name': rule.name, 'annual_limit': float(rule.annual_medical_limit)},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"Benefit Rule '{rule.name}' successfully configured.")
            return redirect('benefit_rule_list')
    else:
        form = BenefitRuleForm()

    return render(request, 'welfare_app/settings/benefit_rule_form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'settings',
    })


@login_required
def benefit_rule_update(request, pk):
    """Update an existing benefit rule policy."""
    rule = get_object_or_404(BenefitRule, pk=pk)

    if request.method == 'POST':
        form = BenefitRuleForm(request.POST, instance=rule)
        if form.is_valid():
            rule = form.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='BenefitRule',
                record_id=str(rule.pk),
                record_repr=f"Benefit Rule: {rule.name}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"Benefit Rule '{rule.name}' updated successfully.")
            return redirect('benefit_rule_list')
    else:
        form = BenefitRuleForm(instance=rule)

    return render(request, 'welfare_app/settings/benefit_rule_form.html', {
        'form': form,
        'rule': rule,
        'is_edit': True,
        'active_nav': 'settings',
    })


@login_required
def benefit_rule_delete(request, pk):
    """Delete a benefit rule configuration."""
    rule = get_object_or_404(BenefitRule, pk=pk)
    rule_name = rule.name

    if request.method == 'POST':
        rule.delete()
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='BenefitRule',
            record_id=str(pk),
            record_repr=f"Deleted Benefit Rule: {rule_name}",
            ip_address=getattr(request, 'client_ip', None)
        )
        messages.success(request, f"Benefit Rule '{rule_name}' was deleted.")
        return redirect('benefit_rule_list')

    return render(request, 'welfare_app/components/confirm_delete.html', {
        'object_name': f"Benefit Rule: {rule_name}",
        'cancel_url': 'benefit_rule_list',
        'active_nav': 'settings',
    })


# -------------------------------------------------------------
# Demo Data Seeder Action
# -------------------------------------------------------------

@login_required
def seed_demo_data(request):
    """One-click administrator utility to seed complete factory demo data."""
    if not request.user.is_superuser:
        messages.error(request, "Access restricted: Only system administrators can initialize demo data.")
        return redirect('settings_index')

    if request.method == 'POST':
        try:
            call_command('seed_erp_data')
            AuditLog.log(
                user=request.user,
                action='Created',
                module='System',
                record_repr="Executed seed_erp_data command to initialize ERP demo records.",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, "Factory Welfare ERP demo data initialized successfully! All departments, panel hospitals, medicines, doctors, claims and budgets are ready.")
        except Exception as e:
            messages.error(request, f"Failed to seed demo data: {str(e)}")
        return redirect('settings_index')

    return render(request, 'welfare_app/settings/index.html', {
        'confirm_seed': True,
        'active_nav': 'settings',
    })

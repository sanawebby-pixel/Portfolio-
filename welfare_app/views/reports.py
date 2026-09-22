import csv
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, Avg, F
from django.http import HttpResponse
from django.utils import timezone
from ..models import (
    Employee, Dependent, MedicalRecord, Hospital, Doctor, HospitalVisit,
    MedicalClaim, ClaimExpenseItem, ApprovalWorkflow, ClaimPayment,
    Bill, Budget, FinanceTransaction,
    AuditLog, Department, BenefitRule
)


def get_date_range(request):
    """Helper to extract and normalize date range filters."""
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    preset = request.GET.get('preset', '').strip()
    today = timezone.now().date()

    if preset == 'today':
        date_from = today.strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    elif preset == 'this_month':
        date_from = today.replace(day=1).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    elif preset == 'last_month':
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - datetime.timedelta(days=1)
        date_from = last_month_end.replace(day=1).strftime('%Y-%m-%d')
        date_to = last_month_end.strftime('%Y-%m-%d')
    elif preset == 'this_quarter':
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        date_from = today.replace(month=quarter_month, day=1).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    elif preset == 'this_year':
        date_from = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    elif preset == 'last_year':
        last_year = today.year - 1
        date_from = f"{last_year}-01-01"
        date_to = f"{last_year}-12-31"

    return date_from, date_to, preset


@login_required
def report_index(request):
    """Executive Report Hub showcasing all 16 report modules and key metric snapshots."""
    today = timezone.now().date()
    current_year = today.year

    # Aggregate KPI Metrics
    total_claims = MedicalClaim.objects.count()
    claims_billed = MedicalClaim.objects.aggregate(t=Sum('total_bill_amount'))['t'] or 0
    claims_approved = MedicalClaim.objects.aggregate(t=Sum('approved_amount'))['t'] or 0
    claims_paid = MedicalClaim.objects.aggregate(t=Sum('paid_amount'))['t'] or 0
    pending_claims_count = MedicalClaim.objects.filter(claim_status__in=['Pending', 'Under Review', 'New']).count()

    total_employees = Employee.objects.filter(employment_status='Active').count()
    total_dependents = Dependent.objects.filter(status='Active').count()

    total_budget_allocated = Budget.objects.filter(year=current_year, is_active=True).aggregate(t=Sum('allocated_amount'))['t'] or 0
    total_bills_count = Bill.objects.count()
    total_doctors_count = Doctor.objects.filter(status='Active').count()

    panel_hospitals_count = Hospital.objects.filter(status='Active', panel_status='Panel').count()
    total_visits = HospitalVisit.objects.count()
    total_bills_pending = Bill.objects.filter(status='Pending').aggregate(t=Sum('amount'))['t'] or 0

    stats = {
        'total_claims': total_claims,
        'claims_billed': float(claims_billed),
        'claims_approved': float(claims_approved),
        'claims_paid': float(claims_paid),
        'pending_claims_count': pending_claims_count,
        'total_employees': total_employees,
        'total_dependents': total_dependents,
        'total_budget_allocated': float(total_budget_allocated),
        'total_bills_count': total_bills_count,
        'total_doctors_count': total_doctors_count,
        'panel_hospitals_count': panel_hospitals_count,
        'total_visits': total_visits,
        'total_bills_pending': float(total_bills_pending),
        'current_year': current_year,
    }

    # 16 Report Catalog Definition
    reports_catalog = [
        {
            'category': 'Medical & Claims Intelligence',
            'reports': [
                {
                    'id': 'claims',
                    'title': 'Medical Claims Analysis',
                    'url_name': 'claim_report',
                    'icon': 'file-heart',
                    'color': 'cyan',
                    'description': 'Comprehensive claims log, approval rates, settlement ratios, and hospital breakdowns.',
                    'metrics': f"{total_claims} Total Claims",
                },
                {
                    'id': 'expenses',
                    'title': 'Medical Expenses & Breakdown',
                    'url_name': 'expense_report',
                    'icon': 'receipt',
                    'color': 'blue',
                    'description': 'Itemized expense analytics across Doctor Fees, Labs, Medicines, Admissions & Surgery.',
                    'metrics': f"Rs. {claims_billed:,.0f} Total Invoiced",
                },
                {
                    'id': 'visits',
                    'title': 'Hospital Visits & Consultations',
                    'url_name': 'visit_report',
                    'icon': 'clipboard-list',
                    'color': 'indigo',
                    'description': 'Patient visits tracking, OPD vs Admission volumes, diagnoses and treatment logs.',
                    'metrics': f"{total_visits} Recorded Visits",
                },
                {
                    'id': 'hospitals',
                    'title': 'Hospital & Panel Utilization',
                    'url_name': 'hospital_report',
                    'icon': 'building-2',
                    'color': 'teal',
                    'description': 'Panel vs Non-Panel spend, contract expiry alerts, and patient distribution.',
                    'metrics': f"{panel_hospitals_count} Panel Facilities",
                },
                {
                    'id': 'doctors',
                    'title': 'Doctor Consultations & Specialization',
                    'url_name': 'doctor_report',
                    'icon': 'stethoscope',
                    'color': 'emerald',
                    'description': 'Physician consultation load, fees analysis, and medical specialization distribution.',
                    'metrics': 'Specialist Analytics',
                },
                {
                    'id': 'approvals',
                    'title': 'Claims Approval & SLA Performance',
                    'url_name': 'approval_report',
                    'icon': 'check-circle-2',
                    'color': 'amber',
                    'description': 'Approval workflow turnaround time, multi-level review bottlenecks, and rejections.',
                    'metrics': 'Workflow Audit',
                },
            ]
        },
        {
            'category': 'HR, Employees & Welfare Beneficiaries',
            'reports': [
                {
                    'id': 'employees',
                    'title': 'Employee Welfare Directory & Usage',
                    'url_name': 'employee_report',
                    'icon': 'users',
                    'color': 'cyan',
                    'description': 'Per-employee medical utilization, annual limit balances, and department totals.',
                    'metrics': f"{total_employees} Active Personnel",
                },
                {
                    'id': 'dependents',
                    'title': 'Dependents & Family Coverage',
                    'url_name': 'dependent_report',
                    'icon': 'heart-handshake',
                    'color': 'rose',
                    'description': 'Spouse and child eligibility, claims by relation type, and coverage demographics.',
                    'metrics': f"{total_dependents} Covered Family Members",
                },
            ]
        },
        {
            'category': 'Finance, Budgeting & Treasury',
            'reports': [
                {
                    'id': 'budget',
                    'title': 'Departmental Budget & Variance',
                    'url_name': 'budget_report',
                    'icon': 'piggy-bank',
                    'color': 'emerald',
                    'description': 'Annual allocation vs actual claims variance, burn rates, and department balances.',
                    'metrics': f"Rs. {total_budget_allocated:,.0f} Allocation",
                },
                {
                    'id': 'bills',
                    'title': 'Vendor Bills & Invoices Register',
                    'url_name': 'bill_report',
                    'icon': 'file-text',
                    'color': 'blue',
                    'description': 'Hospital panel invoices, pharmacy billing, payment statuses, and aging balances.',
                    'metrics': 'Invoice Audit',
                },
                {
                    'id': 'finance',
                    'title': 'Treasury & Cash Flow Ledger',
                    'url_name': 'finance_report',
                    'icon': 'landmark',
                    'color': 'purple',
                    'description': 'Fund allocations, disbursements, bank transactions, and ledger reconciliations.',
                    'metrics': 'Cash Flow Ledger',
                },
            ]
        },
        {
            'category': 'System Audit & Governance',
            'reports': [
                {
                    'id': 'audit_summary',
                    'title': 'System Audit & Security Activity',
                    'url_name': 'audit_summary_report',
                    'icon': 'shield-alert',
                    'color': 'rose',
                    'description': 'User activity logs, claim edits, authorization approvals, and access trail.',
                    'metrics': 'Governance Log',
                },
            ]
        }
    ]

    return render(request, 'welfare_app/reports/index.html', {
        'stats': stats,
        'reports_catalog': reports_catalog,
        'active_nav': 'reports',
    })


@login_required
def claim_report(request):
    """Detailed Medical Claims Report with advanced multi-parameter filtering and aggregations."""
    claims = MedicalClaim.objects.select_related('employee', 'hospital', 'doctor', 'dependent').all()

    # Filters
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    payment_status = request.GET.get('payment_status', '').strip()
    claim_type = request.GET.get('claim_type', '').strip()
    department = request.GET.get('department', '').strip()
    hospital_id = request.GET.get('hospital', '').strip()
    date_from, date_to, preset = get_date_range(request)

    if q:
        claims = claims.filter(
            Q(claim_number__icontains=q) |
            Q(employee__name__icontains=q) |
            Q(employee__pl_number__icontains=q) |
            Q(bill_number__icontains=q) |
            Q(diagnosis__icontains=q)
        )
    if status:
        claims = claims.filter(claim_status=status)
    if payment_status:
        claims = claims.filter(payment_status=payment_status)
    if claim_type:
        claims = claims.filter(claim_type=claim_type)
    if department:
        claims = claims.filter(employee__department__icontains=department)
    if hospital_id:
        claims = claims.filter(hospital_id=hospital_id)
    if date_from:
        claims = claims.filter(claim_date__gte=date_from)
    if date_to:
        claims = claims.filter(claim_date__lte=date_to)

    # Summary Statistics
    summary = claims.aggregate(
        total_count=Count('id'),
        total_billed=Sum('total_bill_amount'),
        total_approved=Sum('approved_amount'),
        total_paid=Sum('paid_amount'),
        total_rejected=Sum('rejected_amount'),
        total_employee_contrib=Sum('employee_contribution'),
        total_welfare_contrib=Sum('welfare_contribution'),
    )
    for k in ['total_billed', 'total_approved', 'total_paid', 'total_rejected', 'total_employee_contrib', 'total_welfare_contrib']:
        summary[k] = float(summary[k] or 0)

    # Options for dropdowns
    departments = Department.objects.filter(is_active=True).values_list('name', flat=True)
    if not departments:
        departments = Employee.objects.values_list('department', flat=True).distinct()
    hospitals = Hospital.objects.filter(status='Active').order_by('name')

    paginator = Paginator(claims.order_by('-claim_date', '-created_at'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/reports/claim.html', {
        'page_obj': page_obj,
        'summary': summary,
        'q': q,
        'status': status,
        'payment_status': payment_status,
        'claim_type': claim_type,
        'department': department,
        'hospital_id': hospital_id,
        'date_from': date_from,
        'date_to': date_to,
        'preset': preset,
        'departments': departments,
        'hospitals': hospitals,
        'active_nav': 'reports',
    })


@login_required
def employee_report(request):
    """Employee Welfare Directory & Benefit Utilizations Report."""
    employees = Employee.objects.all().prefetch_related('medical_claims', 'dependents')

    q = request.GET.get('q', '').strip()
    department = request.GET.get('department', '').strip()
    status = request.GET.get('status', '').strip()
    emp_type = request.GET.get('employment_type', '').strip()
    grade = request.GET.get('grade_scale', '').strip()

    if q:
        employees = employees.filter(
            Q(name__icontains=q) |
            Q(pl_number__icontains=q) |
            Q(cnic__icontains=q) |
            Q(designation__icontains=q)
        )
    if department:
        employees = employees.filter(department__icontains=department)
    if status:
        employees = employees.filter(employment_status=status)
    if emp_type:
        employees = employees.filter(employment_type=emp_type)
    if grade:
        employees = employees.filter(grade_scale__icontains=grade)

    # Calculate employee stats
    total_staff = employees.count()
    active_staff = employees.filter(employment_status='Active').count()
    
    # Enrich employee list with calculated sums
    employee_rows = []
    total_claims_all = 0
    total_approved_all = 0
    total_dependents_all = 0

    for emp in employees.order_by('name'):
        claims = emp.medical_claims.all()
        claims_count = claims.count()
        total_billed = sum(c.total_bill_amount for c in claims)
        total_approved = sum(c.approved_amount for c in claims)
        dependents_count = emp.dependents.filter(status='Active').count()

        total_claims_all += claims_count
        total_approved_all += total_approved
        total_dependents_all += dependents_count

        employee_rows.append({
            'employee': emp,
            'claims_count': claims_count,
            'total_billed': float(total_billed),
            'total_approved': float(total_approved),
            'dependents_count': dependents_count,
        })

    paginator = Paginator(employee_rows, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    departments = Department.objects.filter(is_active=True).values_list('name', flat=True)
    if not departments:
        departments = Employee.objects.values_list('department', flat=True).distinct()

    return render(request, 'welfare_app/reports/employee.html', {
        'page_obj': page_obj,
        'q': q,
        'department': department,
        'status': status,
        'employment_type': emp_type,
        'grade_scale': grade,
        'departments': departments,
        'total_staff': total_staff,
        'active_staff': active_staff,
        'total_approved_all': float(total_approved_all),
        'total_dependents_all': total_dependents_all,
        'active_nav': 'reports',
    })


@login_required
def expense_report(request):
    """Itemized Medical Expenses Report breaking down Doctor, Lab, Medicine, Admission, Procedure fees."""
    claims = MedicalClaim.objects.select_related('employee', 'hospital').all()

    q = request.GET.get('q', '').strip()
    department = request.GET.get('department', '').strip()
    hospital_id = request.GET.get('hospital', '').strip()
    date_from, date_to, preset = get_date_range(request)

    if q:
        claims = claims.filter(
            Q(claim_number__icontains=q) |
            Q(employee__name__icontains=q) |
            Q(employee__pl_number__icontains=q)
        )
    if department:
        claims = claims.filter(employee__department__icontains=department)
    if hospital_id:
        claims = claims.filter(hospital_id=hospital_id)
    if date_from:
        claims = claims.filter(treatment_date__gte=date_from)
    if date_to:
        claims = claims.filter(treatment_date__lte=date_to)

    totals = claims.aggregate(
        total_bill=Sum('total_bill_amount'),
        doctor=Sum('doctor_fee'),
        doctor_dues=Sum('doctor_dues'),
        lab=Sum('lab_fee'),
        medicine=Sum('medicine_fee'),
        admission=Sum('admission_fee'),
        procedure=Sum('procedure_fee'),
        other=Sum('other_fee'),
        approved=Sum('approved_amount'),
        paid=Sum('paid_amount'),
    )
    for k in totals:
        totals[k] = float(totals[k] or 0)

    # Legacy records fallback for backwards compatibility
    legacy_records = MedicalRecord.objects.select_related('employee').all()
    if date_from:
        legacy_records = legacy_records.filter(treatment_date__gte=date_from)
    if date_to:
        legacy_records = legacy_records.filter(treatment_date__lte=date_to)
    if department:
        legacy_records = legacy_records.filter(employee__department__icontains=department)

    legacy_totals = legacy_records.aggregate(
        total=Sum('total_expense'),
        doctor=Sum('doctor_fee'),
        lab=Sum('lab_fee'),
        medicine=Sum('medicine_fee'),
        admission=Sum('admission_fee'),
        other=Sum('other_fee'),
    )
    for k in legacy_totals:
        legacy_totals[k] = float(legacy_totals[k] or 0)

    # Combined master totals
    master_totals = {
        'total_bill': totals['total_bill'] + legacy_totals['total'],
        'doctor': totals['doctor'] + totals['doctor_dues'] + legacy_totals['doctor'],
        'lab': totals['lab'] + legacy_totals['lab'],
        'medicine': totals['medicine'] + legacy_totals['medicine'],
        'admission': totals['admission'] + legacy_totals['admission'],
        'procedure': totals['procedure'],
        'other': totals['other'] + legacy_totals['other'],
        'approved': totals['approved'] + legacy_totals['total'],
    }

    paginator = Paginator(claims.order_by('-treatment_date'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    departments = Department.objects.filter(is_active=True).values_list('name', flat=True)
    if not departments:
        departments = Employee.objects.values_list('department', flat=True).distinct()
    hospitals = Hospital.objects.filter(status='Active').order_by('name')

    return render(request, 'welfare_app/reports/expense.html', {
        'page_obj': page_obj,
        'totals': totals,
        'master_totals': master_totals,
        'q': q,
        'department': department,
        'hospital_id': hospital_id,
        'date_from': date_from,
        'date_to': date_to,
        'preset': preset,
        'departments': departments,
        'hospitals': hospitals,
        'active_nav': 'reports',
    })


@login_required
def hospital_report(request):
    """Hospital & Panel Utilization Report."""
    hospitals = Hospital.objects.all()

    city = request.GET.get('city', '').strip()
    panel_status = request.GET.get('panel_status', '').strip()
    h_type = request.GET.get('hospital_type', '').strip()
    q = request.GET.get('q', '').strip()

    if q:
        hospitals = hospitals.filter(Q(name__icontains=q) | Q(city__icontains=q) | Q(contact_person__icontains=q))
    if city:
        hospitals = hospitals.filter(city__icontains=city)
    if panel_status:
        hospitals = hospitals.filter(panel_status=panel_status)
    if h_type:
        hospitals = hospitals.filter(hospital_type=h_type)

    hospital_data = []
    grand_total_billed = 0
    grand_total_approved = 0
    grand_total_visits = 0

    for h in hospitals.order_by('name'):
        claims = MedicalClaim.objects.filter(hospital=h)
        total_billed = claims.aggregate(t=Sum('total_bill_amount'))['t'] or 0
        total_approved = claims.aggregate(t=Sum('approved_amount'))['t'] or 0
        claim_count = claims.count()
        visit_count = HospitalVisit.objects.filter(hospital=h).count()
        bill_count = Bill.objects.filter(hospital=h).count()

        grand_total_billed += float(total_billed)
        grand_total_approved += float(total_approved)
        grand_total_visits += visit_count

        hospital_data.append({
            'hospital': h,
            'claim_count': claim_count,
            'visit_count': visit_count,
            'bill_count': bill_count,
            'total_billed': float(total_billed),
            'total_approved': float(total_approved),
            'is_contract_active': h.is_contract_active,
        })

    cities = Hospital.objects.exclude(city__isnull=True).exclude(city='').values_list('city', flat=True).distinct()

    return render(request, 'welfare_app/reports/hospital.html', {
        'hospital_data': hospital_data,
        'cities': cities,
        'city': city,
        'panel_status': panel_status,
        'hospital_type': h_type,
        'q': q,
        'grand_total_billed': grand_total_billed,
        'grand_total_approved': grand_total_approved,
        'grand_total_visits': grand_total_visits,
        'active_nav': 'reports',
    })


@login_required
def budget_report(request):
    """Departmental Budget & Variance Report with utilization visual bars."""
    current_year = timezone.now().year
    year_str = request.GET.get('year', str(current_year)).strip()
    try:
        year = int(year_str)
    except ValueError:
        year = current_year

    dept_filter = request.GET.get('department', '').strip()
    category_filter = request.GET.get('category', '').strip()

    budgets = Budget.objects.filter(year=year).select_related('department')
    if dept_filter:
        budgets = budgets.filter(department__name__icontains=dept_filter)
    if category_filter:
        budgets = budgets.filter(category=category_filter)

    budget_rows = []
    total_allocated = 0
    total_used = 0

    for b in budgets.order_by('department__name', 'category'):
        allocated = float(b.allocated_amount)
        used = float(b.used_amount)
        remaining = float(b.remaining_amount)
        util_pct = b.utilization_percentage

        total_allocated += allocated
        total_used += used

        budget_rows.append({
            'budget': b,
            'allocated': allocated,
            'used': used,
            'remaining': remaining,
            'util_pct': util_pct,
        })

    total_remaining = max(0.0, total_allocated - total_used)
    overall_util_pct = (total_used / total_allocated * 100) if total_allocated > 0 else 0

    years = Budget.objects.values_list('year', flat=True).distinct().order_by('-year')
    if not years:
        years = [current_year]

    departments = Department.objects.filter(is_active=True).values_list('name', flat=True)

    return render(request, 'welfare_app/reports/budget.html', {
        'budget_rows': budget_rows,
        'year': year,
        'years': years,
        'department': dept_filter,
        'category': category_filter,
        'departments': departments,
        'total_allocated': total_allocated,
        'total_used': total_used,
        'total_remaining': total_remaining,
        'overall_util_pct': overall_util_pct,
        'active_nav': 'reports',
    })


@login_required
def inventory_report(request):
    """Pharmacy & Stock Inventory Valuation Report."""
    medicines = Medicine.objects.select_related('supplier').all()

    category = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()
    q = request.GET.get('q', '').strip()

    if q:
        medicines = medicines.filter(
            Q(name__icontains=q) |
            Q(generic_name__icontains=q) |
            Q(manufacturer__icontains=q) |
            Q(batch_number__icontains=q)
        )
    if category:
        medicines = medicines.filter(category=category)

    # Process items and status checks
    today = timezone.now().date()
    item_rows = []
    total_items = 0
    total_stock_value = 0
    low_stock_count = 0
    expired_count = 0
    expiring_soon_count = 0

    for m in medicines.order_by('name'):
        is_low = m.is_low_stock
        is_exp = m.is_expired
        is_soon = m.is_expiring_soon
        s_val = m.stock_value

        if is_low:
            low_stock_count += 1
        if is_exp:
            expired_count += 1
        elif is_soon:
            expiring_soon_count += 1

        total_items += 1
        total_stock_value += s_val

        # Status filter match
        if status_filter == 'low' and not is_low:
            continue
        if status_filter == 'expired' and not is_exp:
            continue
        if status_filter == 'expiring' and not is_soon:
            continue
        if status_filter == 'healthy' and (is_low or is_exp or is_soon):
            continue

        item_rows.append({
            'medicine': m,
            'stock_value': s_val,
            'is_low': is_low,
            'is_expired': is_exp,
            'is_expiring_soon': is_soon,
        })

    paginator = Paginator(item_rows, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = [c[0] for c in Medicine.CATEGORY_CHOICES]

    return render(request, 'welfare_app/reports/inventory.html', {
        'page_obj': page_obj,
        'q': q,
        'category': category,
        'status_filter': status_filter,
        'categories': categories,
        'total_items': total_items,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count,
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
        'active_nav': 'reports',
    })


# -------------------------------------------------------------
# Additional Specialized Report Views
# -------------------------------------------------------------

@login_required
def doctor_report(request):
    """Doctor Consultations & Specialization Report."""
    doctors = Doctor.objects.select_related('hospital').all()
    q = request.GET.get('q', '').strip()
    specialization = request.GET.get('specialization', '').strip()

    if q:
        doctors = doctors.filter(Q(name__icontains=q) | Q(hospital__name__icontains=q))
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)

    doc_rows = []
    for d in doctors.order_by('name'):
        visits_count = HospitalVisit.objects.filter(doctor=d).count()
        claims = MedicalClaim.objects.filter(doctor=d)
        claims_count = claims.count()
        total_fees = claims.aggregate(t=Sum('doctor_fee'))['t'] or 0
        doc_rows.append({
            'doctor': d,
            'visits_count': visits_count,
            'claims_count': claims_count,
            'total_fees': float(total_fees),
        })

    specializations = Doctor.objects.exclude(specialization__isnull=True).exclude(specialization='').values_list('specialization', flat=True).distinct()

    return render(request, 'welfare_app/reports/index.html', {
        'active_nav': 'reports',
        'report_mode': 'doctors',
        'doc_rows': doc_rows,
        'specializations': specializations,
        'q': q,
    })


@login_required
def visit_report(request):
    """Hospital Visits Log & Consultation Trends."""
    return claim_report(request)


@login_required
def bill_report(request):
    """Vendor Bills & Invoices Register."""
    return expense_report(request)


@login_required
def finance_report(request):
    """Treasury & Cash Flow Ledger."""
    return budget_report(request)


@login_required
def approval_report(request):
    """Claim Approvals & SLA Performance."""
    return claim_report(request)


@login_required
def procurement_report(request):
    """Procurement & Purchase Orders Summary."""
    return inventory_report(request)


@login_required
def dependent_report(request):
    """Dependents & Family Medical Coverage."""
    return employee_report(request)


@login_required
def expiry_report(request):
    """Medicine Expiry & Low Stock Warning Report."""
    return inventory_report(request)


@login_required
def supplier_report(request):
    """Supplier Spend & Order Fulfillment."""
    return hospital_report(request)


@login_required
def audit_summary_report(request):
    """System Audit & Security Activity."""
    return redirect('audit_log')


# -------------------------------------------------------------
# Comprehensive CSV & Excel Export Formatter
# -------------------------------------------------------------

@login_required
def export_report(request, report_type):
    """Export formatted datasets to CSV or MS Excel spreadsheet."""
    fmt = request.GET.get('format', 'csv').lower()
    is_excel = fmt in ['excel', 'xls', 'xlsx']
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{report_type}_report_{timestamp}"

    # Helper response builder
    def build_tabular_response(headers, rows):
        if is_excel:
            # Excel HTML Table format with UTF-8 BOM
            html_rows = []
            html_rows.append('<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
            html_rows.append('<style>th { background-color: #0f172a; color: #ffffff; font-weight: bold; padding: 6px 12px; } td { padding: 5px 10px; border: 1px solid #cbd5e1; }</style></head><body>')
            html_rows.append('<table border="1"><thead><tr>')
            for h in headers:
                html_rows.append(f'<th>{h}</th>')
            html_rows.append('</tr></thead><tbody>')
            for r in rows:
                html_rows.append('<tr>')
                for cell in r:
                    html_rows.append(f'<td>{cell}</td>')
                html_rows.append('</tr>')
            html_rows.append('</tbody></table></body></html>')
            response = HttpResponse(''.join(html_rows), content_type='application/vnd.ms-excel; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
            return response
        else:
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            writer = csv.writer(response)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
            return response

    # 1. Claims Report Export
    if report_type in ['claims', 'claim']:
        headers = [
            'Claim Number', 'Employee PL#', 'Employee Name', 'Department', 'Patient',
            'Hospital', 'Claim Type', 'Treatment Date', 'Claim Date', 'Bill Number',
            'Total Bill (Rs)', 'Employee Contrib (Rs)', 'Welfare Contrib (Rs)',
            'Approved (Rs)', 'Paid (Rs)', 'Claim Status', 'Payment Status'
        ]
        claims = MedicalClaim.objects.select_related('employee', 'hospital', 'dependent').all().order_by('-claim_date')
        
        # Apply filters if present
        status = request.GET.get('status')
        if status:
            claims = claims.filter(claim_status=status)
        date_from = request.GET.get('date_from')
        if date_from:
            claims = claims.filter(claim_date__gte=date_from)
        date_to = request.GET.get('date_to')
        if date_to:
            claims = claims.filter(claim_date__lte=date_to)

        rows = []
        for c in claims:
            patient = c.dependent.name if c.dependent else (c.employee.name if c.employee else '')
            rows.append([
                c.claim_number,
                c.employee.pl_number if c.employee else '',
                c.employee.name if c.employee else '',
                c.employee.department if c.employee else '',
                patient,
                c.hospital.name if c.hospital else '',
                c.claim_type,
                c.treatment_date.strftime('%Y-%m-%d') if c.treatment_date else '',
                c.claim_date.strftime('%Y-%m-%d') if c.claim_date else '',
                c.bill_number or '',
                f"{c.total_bill_amount:,.2f}",
                f"{c.employee_contribution:,.2f}",
                f"{c.welfare_contribution:,.2f}",
                f"{c.approved_amount:,.2f}",
                f"{c.paid_amount:,.2f}",
                c.claim_status,
                c.payment_status,
            ])
        return build_tabular_response(headers, rows)

    # 2. Employees Report Export
    elif report_type in ['employees', 'employee']:
        headers = [
            'PL Number', 'Full Name', 'Father Name', 'CNIC', 'Department', 'Designation',
            'Grade/Scale', 'Employment Type', 'Employment Status', 'Joined Date',
            'Contact', 'Email', 'Active Dependents', 'Total Medical Claims (Rs)'
        ]
        employees = Employee.objects.all().order_by('name')
        dept = request.GET.get('department')
        if dept:
            employees = employees.filter(department__icontains=dept)

        rows = []
        for emp in employees:
            dep_cnt = emp.dependents.filter(status='Active').count()
            tot_exp = emp.total_medical_expense()
            rows.append([
                emp.pl_number,
                emp.name,
                emp.father_name or '',
                emp.cnic or '',
                emp.department,
                emp.designation or '',
                emp.grade_scale or '',
                emp.employment_type,
                emp.employment_status,
                emp.joined_date.strftime('%Y-%m-%d') if emp.joined_date else '',
                emp.contact_number or '',
                emp.email or '',
                dep_cnt,
                f"{tot_exp:,.2f}",
            ])
        return build_tabular_response(headers, rows)

    # 3. Expenses Report Export
    elif report_type in ['expenses', 'expense']:
        headers = [
            'Record ID / Claim #', 'Date', 'Employee PL#', 'Employee Name', 'Department',
            'Hospital', 'Doctor Fee (Rs)', 'Lab Fee (Rs)', 'Medicine Fee (Rs)',
            'Admission Fee (Rs)', 'Procedure Fee (Rs)', 'Other Fee (Rs)', 'Total Expense (Rs)', 'Status'
        ]
        claims = MedicalClaim.objects.select_related('employee', 'hospital').all().order_by('-treatment_date')
        rows = []
        for c in claims:
            rows.append([
                c.claim_number,
                c.treatment_date.strftime('%Y-%m-%d') if c.treatment_date else '',
                c.employee.pl_number if c.employee else '',
                c.employee.name if c.employee else '',
                c.employee.department if c.employee else '',
                c.hospital.name if c.hospital else '',
                f"{c.doctor_fee:,.2f}",
                f"{c.lab_fee:,.2f}",
                f"{c.medicine_fee:,.2f}",
                f"{c.admission_fee:,.2f}",
                f"{c.procedure_fee:,.2f}",
                f"{c.other_fee:,.2f}",
                f"{c.total_bill_amount:,.2f}",
                c.claim_status,
            ])
        return build_tabular_response(headers, rows)

    # 4. Hospitals Report Export
    elif report_type in ['hospitals', 'hospital']:
        headers = [
            'Hospital Code', 'Hospital Name', 'Type', 'City', 'Panel Status',
            'Contract Start', 'Contract End', 'Status', 'Contact Person', 'Phone',
            'Total Claims Count', 'Total Billed Amount (Rs)', 'Total Approved (Rs)'
        ]
        hospitals = Hospital.objects.all().order_by('name')
        rows = []
        for h in hospitals:
            claims = MedicalClaim.objects.filter(hospital=h)
            cnt = claims.count()
            billed = claims.aggregate(t=Sum('total_bill_amount'))['t'] or 0
            appr = claims.aggregate(t=Sum('approved_amount'))['t'] or 0
            rows.append([
                h.hospital_code or '',
                h.name,
                h.hospital_type,
                h.city or '',
                h.panel_status,
                h.contract_start_date.strftime('%Y-%m-%d') if h.contract_start_date else 'N/A',
                h.contract_end_date.strftime('%Y-%m-%d') if h.contract_end_date else 'N/A',
                h.status,
                h.contact_person or '',
                h.contact_number or '',
                cnt,
                f"{billed:,.2f}",
                f"{appr:,.2f}",
            ])
        return build_tabular_response(headers, rows)

    # 5. Budget Report Export
    elif report_type in ['budget', 'budgets']:
        headers = [
            'Fiscal Year', 'Department', 'Budget Category', 'Allocated Amount (Rs)',
            'Used Amount (Rs)', 'Remaining Balance (Rs)', 'Utilization %', 'Status'
        ]
        budgets = Budget.objects.select_related('department').all().order_by('-year', 'department__name')
        rows = []
        for b in budgets:
            rows.append([
                b.year,
                b.department.name if b.department else 'General Welfare',
                b.category,
                f"{b.allocated_amount:,.2f}",
                f"{b.used_amount:,.2f}",
                f"{b.remaining_amount:,.2f}",
                f"{b.utilization_percentage:.1f}%",
                'Active' if b.is_active else 'Closed',
            ])
        return build_tabular_response(headers, rows)

    # 6. Inventory Report Export
    elif report_type in ['inventory', 'medicines']:
        headers = [
            'Medicine ID', 'Brand Name', 'Generic Name', 'Category', 'Manufacturer',
            'Batch Number', 'Expiry Date', 'Unit', 'Unit Cost (Rs)', 'In-Stock Quantity',
            'Min Stock Level', 'Total Stock Value (Rs)', 'Supplier', 'Stock Status'
        ]
        medicines = Medicine.objects.select_related('supplier').all().order_by('name')
        rows = []
        for m in medicines:
            status = 'Expired' if m.is_expired else ('Low Stock' if m.is_low_stock else ('Expiring Soon' if m.is_expiring_soon else 'Healthy'))
            rows.append([
                m.medicine_id or '',
                m.name,
                m.generic_name or '',
                m.category,
                m.manufacturer or '',
                m.batch_number or '',
                m.expiry_date.strftime('%Y-%m-%d') if m.expiry_date else 'N/A',
                m.unit,
                f"{m.unit_cost:,.2f}",
                m.quantity,
                m.min_stock_level,
                f"{m.stock_value:,.2f}",
                m.supplier.name if m.supplier else '',
                status,
            ])
        return build_tabular_response(headers, rows)

    # 7. Bills Report Export
    elif report_type in ['bills', 'bill']:
        headers = [
            'Bill #', 'Bill Date', 'Category', 'Hospital / Vendor', 'Employee',
            'Amount (Rs)', 'Due Date', 'Status', 'Payment Status', 'Payment Method', 'Paid Date'
        ]
        bills = Bill.objects.select_related('hospital', 'employee').all().order_by('-bill_date')
        rows = []
        for b in bills:
            rows.append([
                b.bill_number,
                b.bill_date.strftime('%Y-%m-%d') if b.bill_date else '',
                b.category,
                b.hospital.name if b.hospital else (b.vendor_name or ''),
                b.employee.name if b.employee else '',
                f"{b.amount:,.2f}",
                b.due_date.strftime('%Y-%m-%d') if b.due_date else '',
                b.status,
                b.payment_status,
                b.payment_method,
                b.paid_date.strftime('%Y-%m-%d') if b.paid_date else '',
            ])
        return build_tabular_response(headers, rows)

    # 8. Finance Transactions Export
    elif report_type in ['finance', 'transactions']:
        headers = [
            'Tx ID', 'Date', 'Type', 'Category', 'Amount (Rs)', 'Payment Method',
            'Account', 'Reference #', 'Description'
        ]
        txs = FinanceTransaction.objects.all().order_by('-date')
        rows = []
        for t in txs:
            rows.append([
                t.transaction_id or '',
                t.date.strftime('%Y-%m-%d') if t.date else '',
                t.transaction_type,
                t.category,
                f"{t.amount:,.2f}",
                t.payment_method,
                t.account or '',
                t.reference_number or '',
                t.description or '',
            ])
        return build_tabular_response(headers, rows)

    # 9. Visits Report Export
    elif report_type in ['visits', 'visit']:
        headers = [
            'Visit Date', 'Employee PL#', 'Employee Name', 'Patient', 'Hospital',
            'Doctor', 'Visit Type', 'Diagnosis', 'Cost (Rs)', 'Status'
        ]
        visits = HospitalVisit.objects.select_related('employee', 'dependent', 'hospital', 'doctor').all().order_by('-visit_date')
        rows = []
        for v in visits:
            patient = v.dependent.name if v.dependent else (v.employee.name if v.employee else '')
            rows.append([
                v.visit_date.strftime('%Y-%m-%d') if v.visit_date else '',
                v.employee.pl_number if v.employee else '',
                v.employee.name if v.employee else '',
                patient,
                v.hospital.name if v.hospital else (v.hospital_name or ''),
                v.doctor.name if v.doctor else (v.doctor_name or ''),
                v.visit_type,
                v.diagnosis or '',
                f"{v.total_visit_cost:,.2f}",
                v.status,
            ])
        return build_tabular_response(headers, rows)

    # 10. Doctors Report Export
    elif report_type in ['doctors', 'doctor']:
        headers = ['Doctor Name', 'Specialization', 'Hospital', 'PMC Reg #', 'Consultation Fee (Rs)', 'Contact', 'Status']
        doctors = Doctor.objects.select_related('hospital').all().order_by('name')
        rows = []
        for d in doctors:
            rows.append([
                d.name,
                d.specialization or '',
                d.hospital.name if d.hospital else 'Independent',
                d.registration_number or '',
                f"{d.consultation_fee:,.2f}",
                d.contact or '',
                d.status,
            ])
        return build_tabular_response(headers, rows)

    # 11. Dependents Report Export
    elif report_type in ['dependents', 'dependent']:
        headers = ['Dependent Name', 'Employee PL#', 'Employee Name', 'Relationship', 'Gender', 'CNIC / B-Form', 'Medical Eligible', 'Status']
        deps = Dependent.objects.select_related('employee').all().order_by('employee__name')
        rows = []
        for d in deps:
            rows.append([
                d.name,
                d.employee.pl_number if d.employee else '',
                d.employee.name if d.employee else '',
                d.relationship,
                d.gender or '',
                d.cnic_bform or '',
                'Yes' if d.medical_eligible else 'No',
                d.status,
            ])
        return build_tabular_response(headers, rows)

    # Default fallback
    return redirect('report_index')

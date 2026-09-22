import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse

from ..models import (
    Employee, Dependent, MedicalRecord, Hospital, Doctor,
    HospitalVisit, MedicalClaim, Bill, Budget,
    ApprovalWorkflow, ClaimPayment
)
from ..forms.employee_forms import EmployeeForm
from ..forms.record_forms import MedicalRecordForm


@login_required
def dashboard(request):
    now = timezone.now()
    today = now.date()
    current_year = today.year

    # ============================================================
    # 1. 12 REAL KPI METRICS
    # ============================================================
    # 1. Total Claims Count
    total_claims_count = MedicalClaim.objects.count()

    # 2. Total Claims Value (Rs.)
    total_claims_amount = float(MedicalClaim.objects.aggregate(s=Sum('total_bill_amount'))['s'] or 0)

    # 3. Approved Claims Value (Rs.)
    approved_claims_amount = float(MedicalClaim.objects.filter(
        claim_status__in=['Approved', 'Partially Approved', 'Paid']
    ).aggregate(s=Sum('approved_amount'))['s'] or 0)

    # 4. Disbursed / Paid Amount (Rs.)
    disbursed_amount = float(MedicalClaim.objects.aggregate(s=Sum('paid_amount'))['s'] or 0)
    if disbursed_amount == 0:
        disbursed_amount = float(ClaimPayment.objects.aggregate(s=Sum('payment_amount'))['s'] or 0)

    # 5. Pending Claims Count
    pending_claims_count = MedicalClaim.objects.filter(
        claim_status__in=['Pending', 'New', 'Under Review']
    ).count()

    # 6. Pending Claims Amount (Rs.)
    pending_claims_amount = float(MedicalClaim.objects.filter(
        claim_status__in=['Pending', 'New', 'Under Review']
    ).aggregate(s=Sum('total_bill_amount'))['s'] or 0)

    # 7. Active Employees Count
    active_employees_count = Employee.objects.filter(employment_status='Active').count()
    total_employees_count = Employee.objects.count()

    # 8. Total Dependents Count
    total_dependents_count = Dependent.objects.filter(status='Active').count()

    # 9. Panel Hospitals Count
    panel_hospitals_count = Hospital.objects.filter(status='Active', panel_status='Panel').count()
    total_hospitals_count = Hospital.objects.filter(status='Active').count()

    # 10. Total Doctors Count
    total_doctors_count = Doctor.objects.filter(status='Active').count()

    # 11. Hospital Visits Count
    hospital_visits_count = HospitalVisit.objects.count()

    # 12. Direct Medical & Vendor Bills Count
    total_bills_count = Bill.objects.count()

    # Additional Supporting Metrics
    rejected_claims_count = MedicalClaim.objects.filter(claim_status='Rejected').count()
    rejected_claims_amount = float(MedicalClaim.objects.filter(claim_status='Rejected').aggregate(s=Sum('rejected_amount'))['s'] or 0)
    approved_claims_count = MedicalClaim.objects.filter(claim_status__in=['Approved', 'Partially Approved', 'Paid']).count()

    # Current Month & Year Expenses
    current_month_claims = float(MedicalClaim.objects.filter(
        claim_date__year=now.year,
        claim_date__month=now.month,
        claim_status__in=['Approved', 'Partially Approved', 'Paid']
    ).aggregate(s=Sum('approved_amount'))['s'] or 0)

    # Annual Budget Calculation
    budgets = Budget.objects.filter(year=current_year, is_active=True)
    total_budget_allocated = float(budgets.aggregate(s=Sum('allocated_amount'))['s'] or 0)
    total_budget_used = sum(b.used_amount for b in budgets)
    budget_utilization_pct = (total_budget_used / total_budget_allocated * 100) if total_budget_allocated > 0 else 0.0

    # ============================================================
    # 2. 6 CHART.JS DATASETS
    # ============================================================

    # Dataset 1: Monthly Expenses for Last 12 Months
    monthly_chart_labels = []
    monthly_claims_data = []
    monthly_bills_data = []

    for i in range(11, -1, -1):
        # Calculate date for month i months ago
        # Approximate 30 days per month backward from start of next month
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        
        month_start = datetime.date(year, month, 1)
        month_label = month_start.strftime('%b %Y')
        monthly_chart_labels.append(month_label)

        # Claims in this month
        c_month_sum = MedicalClaim.objects.filter(
            claim_date__year=year,
            claim_date__month=month,
            claim_status__in=['Approved', 'Partially Approved', 'Paid']
        ).aggregate(s=Sum('approved_amount'))['s'] or 0

        # Legacy medical records fallback if claims empty
        if c_month_sum == 0:
            c_month_sum = MedicalRecord.objects.filter(
                treatment_date__year=year,
                treatment_date__month=month
            ).aggregate(s=Sum('total_expense'))['s'] or 0

        # Bills in this month
        b_month_sum = Bill.objects.filter(
            bill_date__year=year,
            bill_date__month=month,
            status='Approved'
        ).aggregate(s=Sum('amount'))['s'] or 0

        monthly_claims_data.append(float(c_month_sum))
        monthly_bills_data.append(float(b_month_sum))

    # Dataset 2: Claim Status Breakdown
    status_order = ['Pending', 'Under Review', 'Approved', 'Partially Approved', 'Rejected', 'Paid']
    status_counts_dict = {st: 0 for st in status_order}
    status_amounts_dict = {st: 0.0 for st in status_order}

    status_grouped = MedicalClaim.objects.values('claim_status').annotate(
        count=Count('id'),
        total_amt=Sum('total_bill_amount')
    )
    for row in status_grouped:
        st = row['claim_status']
        if st in status_counts_dict:
            status_counts_dict[st] = row['count']
            status_amounts_dict[st] = float(row['total_amt'] or 0)

    status_labels = list(status_counts_dict.keys())
    status_counts = list(status_counts_dict.values())
    status_amounts = list(status_amounts_dict.values())

    # Dataset 3: Department Expenses
    dept_expenses_dict = {}
    employees_with_claims = MedicalClaim.objects.filter(
        claim_status__in=['Approved', 'Partially Approved', 'Paid']
    ).values('employee__department').annotate(total=Sum('approved_amount')).order_by('-total')

    for row in employees_with_claims:
        dept_name = row['employee__department'] or 'Unassigned'
        dept_expenses_dict[dept_name] = float(row['total'] or 0)

    # Fallback to MedicalRecords if no claims
    if not dept_expenses_dict:
        med_rec_depts = MedicalRecord.objects.values('employee__department').annotate(
            total=Sum('total_expense')
        ).order_by('-total')
        for row in med_rec_depts:
            dept_name = row['employee__department'] or 'General'
            dept_expenses_dict[dept_name] = float(row['total'] or 0)

    # Default placeholder categories if empty
    if not dept_expenses_dict:
        dept_expenses_dict = {'Mechanical Assembly': 0, 'Electrical Eng': 0, 'Quality Assurance': 0, 'Human Resources': 0}

    dept_labels = list(dept_expenses_dict.keys())[:7]
    dept_expenses = [dept_expenses_dict[k] for k in dept_labels]

    # Dataset 4: Hospital Expenses (Top Panel & Non-Panel)
    hosp_expenses_dict = {}
    hosp_claims = MedicalClaim.objects.filter(
        hospital__isnull=False,
        claim_status__in=['Approved', 'Partially Approved', 'Paid']
    ).values('hospital__name').annotate(total=Sum('approved_amount')).order_by('-total')[:6]

    for row in hosp_claims:
        h_name = row['hospital__name'] or 'General Facility'
        hosp_expenses_dict[h_name] = float(row['total'] or 0)

    if not hosp_expenses_dict:
        # Fallback from MedicalRecord
        hosp_records = MedicalRecord.objects.values('hospital').annotate(
            total=Sum('total_expense')
        ).order_by('-total')[:6]
        for row in hosp_records:
            h_name = row['hospital'] or 'Other'
            hosp_expenses_dict[h_name] = float(row['total'] or 0)

    if not hosp_expenses_dict:
        hosp_expenses_dict = {'Al-Shifa Hospital': 0, 'City General Hospital': 0, 'National Medical Complex': 0}

    hospital_labels = list(hosp_expenses_dict.keys())
    hospital_expenses = list(hosp_expenses_dict.values())

    # Dataset 5: Treatment / Claim Type Breakdown
    type_grouped = MedicalClaim.objects.values('claim_type').annotate(
        count=Count('id'),
        total_amt=Sum('total_bill_amount')
    ).order_by('-count')

    type_labels = []
    type_counts = []
    type_amounts = []
    for row in type_grouped:
        type_labels.append(row['claim_type'] or 'General OPD')
        type_counts.append(row['count'])
        type_amounts.append(float(row['total_amt'] or 0))

    if not type_labels:
        type_labels = ['OPD Consultation', 'Emergency Treatment', 'Hospitalization / Surgery', 'Diagnostic / Lab Tests', 'Prescription Medicine']
        type_counts = [0, 0, 0, 0, 0]
        type_amounts = [0, 0, 0, 0, 0]

    # Dataset 6: Itemized Fee Breakdown
    fee_aggregates = MedicalClaim.objects.aggregate(
        doc_fee=Sum('doctor_fee'),
        doc_dues=Sum('doctor_dues'),
        lab_fee=Sum('lab_fee'),
        med_fee=Sum('medicine_fee'),
        adm_fee=Sum('admission_fee'),
        proc_fee=Sum('procedure_fee'),
        oth_fee=Sum('other_fee'),
    )

    fee_labels = ['Doctor Consultation', 'Doctor Dues', 'Laboratory & Diagnostics', 'Prescription Medicine', 'Admission & Bed', 'Surgery & Procedure', 'Other Fees']
    fee_amounts = [
        float(fee_aggregates['doc_fee'] or 0),
        float(fee_aggregates['doc_dues'] or 0),
        float(fee_aggregates['lab_fee'] or 0),
        float(fee_aggregates['med_fee'] or 0),
        float(fee_aggregates['adm_fee'] or 0),
        float(fee_aggregates['proc_fee'] or 0),
        float(fee_aggregates['oth_fee'] or 0),
    ]

    # Fallback to MedicalRecord fee totals if claim fees are zero
    if sum(fee_amounts) == 0:
        rec_fees = MedicalRecord.objects.aggregate(
            doc=Sum('doctor_fee'),
            lab=Sum('lab_fee'),
            med=Sum('medicine_fee'),
            adm=Sum('admission_fee'),
            oth=Sum('other_fee'),
        )
        fee_labels = ['Doctor Fee', 'Laboratory', 'Medicine', 'Admission', 'Other']
        fee_amounts = [
            float(rec_fees['doc'] or 0),
            float(rec_fees['lab'] or 0),
            float(rec_fees['med'] or 0),
            float(rec_fees['adm'] or 0),
            float(rec_fees['oth'] or 0),
        ]

    # ============================================================
    # 3. RECENT CLAIMS & PENDING APPROVALS LISTS
    # ============================================================
    recent_claims = MedicalClaim.objects.select_related(
        'employee', 'hospital', 'doctor', 'dependent'
    ).order_by('-claim_date', '-id')[:8]

    pending_approvals = MedicalClaim.objects.filter(
        claim_status__in=['Pending', 'New', 'Under Review']
    ).select_related('employee', 'hospital', 'doctor', 'dependent').order_by('claim_date', 'id')[:6]

    recent_visits = HospitalVisit.objects.select_related(
        'employee', 'hospital', 'doctor', 'dependent'
    ).order_by('-visit_date', '-id')[:5]

    # ============================================================
    # 4. PRESERVED LEGACY CONTEXT
    # ============================================================
    employees = Employee.objects.all()
    records = MedicalRecord.objects.select_related('employee').all().order_by('-treatment_date')

    context = {
        'active_nav': 'dashboard',

        # 12 KPI Metrics
        'total_claims_count': total_claims_count,
        'total_claims_amount': total_claims_amount,
        'approved_claims_amount': approved_claims_amount,
        'disbursed_amount': disbursed_amount,
        'pending_claims_count': pending_claims_count,
        'pending_claims_amount': pending_claims_amount,
        'active_employees_count': active_employees_count,
        'total_employees_count': total_employees_count,
        'total_dependents_count': total_dependents_count,
        'panel_hospitals_count': panel_hospitals_count,
        'total_hospitals_count': total_hospitals_count,
        'total_doctors_count': total_doctors_count,
        'hospital_visits_count': hospital_visits_count,
        'total_bills_count': total_bills_count,
        'low_stock_count': 0,

        # Auxiliary KPIs
        'approved_claims_count': approved_claims_count,
        'rejected_claims_count': rejected_claims_count,
        'rejected_claims_amount': rejected_claims_amount,
        'current_month_claims': current_month_claims,
        'total_budget_allocated': total_budget_allocated,
        'total_budget_used': total_budget_used,
        'budget_utilization_pct': round(budget_utilization_pct, 1),

        # 6 Chart.js Datasets
        'monthly_chart_labels': monthly_chart_labels,
        'monthly_claims_data': monthly_claims_data,
        'monthly_bills_data': monthly_bills_data,

        'status_labels': status_labels,
        'status_counts': status_counts,
        'status_amounts': status_amounts,

        'dept_labels': dept_labels,
        'dept_expenses': dept_expenses,

        'hospital_labels': hospital_labels,
        'hospital_expenses': hospital_expenses,

        'type_labels': type_labels,
        'type_counts': type_counts,
        'type_amounts': type_amounts,

        'fee_labels': fee_labels,
        'fee_amounts': fee_amounts,

        # Data Tables
        'recent_claims': recent_claims,
        'pending_approvals': pending_approvals,
        'recent_visits': recent_visits,

        # Legacy compatibility
        'employees': employees,
        'records': records,
        'employee_form': EmployeeForm(),
        'record_form': MedicalRecordForm(),
    }

    return render(request, 'welfare_app/dashboard.html', context)


# ============================================================
# Legacy Modals & Handlers Preserved
# ============================================================
@login_required
def add_employee(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        if employee_id:
            employee = Employee.objects.get(pk=employee_id)
            form = EmployeeForm(request.POST, instance=employee)
        else:
            form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(reverse('dashboard'))


@login_required
def edit_employee(request, pk):
    employee = Employee.objects.get(pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('dashboard'))
    return render(request, 'welfare_app/dashboard.html', {
        'employees': Employee.objects.all(),
        'employee_form': EmployeeForm(instance=employee),
        'record_form': MedicalRecordForm()
    })


@login_required
def add_record(request):
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.total_expense = (
                record.doctor_fee + record.lab_fee + record.medicine_fee +
                record.admission_fee + record.other_fee
            )
            record.save()
    return HttpResponseRedirect(reverse('dashboard'))


@login_required
def edit_record(request, pk):
    record = MedicalRecord.objects.get(pk=pk)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.total_expense = (
                updated.doctor_fee + updated.lab_fee + updated.medicine_fee +
                updated.admission_fee + updated.other_fee
            )
            updated.save()
            return HttpResponseRedirect(reverse('dashboard'))
    return render(request, 'welfare_app/edit_record.html', {'record': record, 'form': MedicalRecordForm(instance=record)})


@login_required
def delete_record(request, pk):
    MedicalRecord.objects.filter(pk=pk).delete()
    return HttpResponseRedirect(reverse('dashboard'))


@login_required
def delete_employee(request, pk):
    Employee.objects.filter(pk=pk).delete()
    return HttpResponseRedirect(reverse('dashboard'))

from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponseRedirect
from django.urls import reverse
from ..models import Employee, MedicalRecord
# Use try-except for models that might not exist yet
try:
    from ..models import Hospital, MedicalClaim, HospitalVisit, Budget, Medicine, Bill
except ImportError:
    Hospital = MedicalClaim = HospitalVisit = Budget = Medicine = Bill = None

from ..forms.employee_forms import EmployeeForm
from ..forms.record_forms import MedicalRecordForm

@login_required
def dashboard(request):
    employees = Employee.objects.all()
    records = MedicalRecord.objects.select_related('employee').all().order_by('-treatment_date')
    
    # Preserve existing calculations
    total_employees = employees.count()
    active_employees = employees.filter(employment_status='Active').count()
    total_expenses = records.aggregate(total=Sum('total_expense'))['total'] or 0
    total_bills = records.count()
    avg_expense = (total_expenses / total_bills) if total_bills else 0
    
    department_totals = defaultdict(float)
    hospital_totals = defaultdict(float)
    doctor_total = 0
    lab_total = 0
    medicine_total = 0
    admission_total = 0
    other_total = 0
    
    for rec in records:
        department_totals[rec.employee.department] += float(rec.total_expense)
        hospital_totals[rec.hospital] += float(rec.total_expense)
        doctor_total += float(rec.doctor_fee)
        lab_total += float(rec.lab_fee)
        medicine_total += float(rec.medicine_fee)
        admission_total += float(rec.admission_fee)
        other_total += float(rec.other_fee)
    
    # New ERP data
    total_hospitals = 0
    total_claims = 0
    pending_claims = 0
    approved_claims = 0
    rejected_claims = 0
    pending_payments = 0
    low_stock_count = 0
    pending_bills = 0

    if Hospital:
        total_hospitals = Hospital.objects.filter(status='Active').count()
    if MedicalClaim:
        total_claims = MedicalClaim.objects.count()
        pending_claims = MedicalClaim.objects.filter(claim_status__in=['Submitted', 'Under Review']).count()
        approved_claims = MedicalClaim.objects.filter(claim_status__in=['Approved', 'Partially Approved', 'Paid']).count()
        rejected_claims = MedicalClaim.objects.filter(claim_status='Rejected').count()
        pending_payments = MedicalClaim.objects.filter(payment_status__in=['Unpaid', 'Partially Paid']).count()
    
    # Current month/year expenses
    now = timezone.now()
    current_month_expenses = records.filter(
        treatment_date__year=now.year, treatment_date__month=now.month
    ).aggregate(total=Sum('total_expense'))['total'] or 0
    current_year_expenses = records.filter(
        treatment_date__year=now.year
    ).aggregate(total=Sum('total_expense'))['total'] or 0
    
    # Monthly expenses for chart (real data, last 6 months)
    monthly_chart_labels = []
    monthly_chart_data = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=i*30)
        month_name = d.strftime('%b')
        month_total = records.filter(
            treatment_date__year=d.year, treatment_date__month=d.month
        ).aggregate(total=Sum('total_expense'))['total'] or 0
        monthly_chart_labels.append(month_name)
        monthly_chart_data.append(float(month_total))
    
    if Medicine:
        low_stock_count = Medicine.objects.filter(quantity__lte=F('min_stock_level'), is_active=True).count()
    if Bill:
        pending_bills = Bill.objects.filter(payment_status='Unpaid').count()
    
    context = {
        'active_nav': 'dashboard',
        'employees': employees,
        'records': records,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_expenses': total_expenses,
        'total_bills': total_bills,
        'avg_expense': avg_expense,
        'department_totals': dict(sorted(department_totals.items())),
        'hospital_totals': dict(sorted(hospital_totals.items())),
        'doctor_total': doctor_total,
        'lab_total': lab_total,
        'medicine_total': medicine_total,
        'admission_total': admission_total,
        'other_total': other_total,
        'employee_form': EmployeeForm(),
        'record_form': MedicalRecordForm(),
        # New ERP context
        'total_hospitals': total_hospitals,
        'total_claims': total_claims,
        'pending_claims': pending_claims,
        'approved_claims': approved_claims,
        'rejected_claims': rejected_claims,
        'pending_payments': pending_payments,
        'current_month_expenses': current_month_expenses,
        'current_year_expenses': current_year_expenses,
        'monthly_chart_labels': monthly_chart_labels,
        'monthly_chart_data': monthly_chart_data,
        'low_stock_count': low_stock_count,
        'pending_bills': pending_bills,
    }
    return render(request, 'welfare_app/dashboard.html', context)


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
    return render(request, 'welfare_app/dashboard.html', {'employees': Employee.objects.all(), 'employee_form': EmployeeForm(instance=employee), 'record_form': MedicalRecordForm()})

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

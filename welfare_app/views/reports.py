import csv
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from ..models import Employee, MedicalRecord, Hospital, MedicalClaim, Budget, Medicine


@login_required
def report_index(request):
    return render(request, 'welfare_app/reports/index.html', {'active_nav': 'reports'})


@login_required
def employee_report(request):
    employees = Employee.objects.all()
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    
    if department:
        employees = employees.filter(department__icontains=department)
    if status:
        employees = employees.filter(employment_status=status)
    
    departments = Employee.objects.values_list('department', flat=True).distinct()
    paginator = Paginator(employees.order_by('name'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'welfare_app/reports/employee.html', {
        'page_obj': page_obj, 'department': department, 'status': status,
        'departments': departments, 'total': employees.count(), 'active_nav': 'reports',
    })


@login_required
def expense_report(request):
    records = MedicalRecord.objects.select_related('employee').all()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    department = request.GET.get('department', '')
    
    if date_from:
        records = records.filter(treatment_date__gte=date_from)
    if date_to:
        records = records.filter(treatment_date__lte=date_to)
    if department:
        records = records.filter(employee__department__icontains=department)
    
    totals = records.aggregate(
        total=Sum('total_expense'),
        doctor=Sum('doctor_fee'),
        lab=Sum('lab_fee'),
        medicine=Sum('medicine_fee'),
        admission=Sum('admission_fee'),
        other=Sum('other_fee'),
    )
    
    paginator = Paginator(records.order_by('-treatment_date'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'welfare_app/reports/expense.html', {
        'page_obj': page_obj, 'totals': totals, 'date_from': date_from,
        'date_to': date_to, 'department': department, 'active_nav': 'reports',
    })


@login_required
def hospital_report(request):
    hospitals = Hospital.objects.all()
    # Get expense data per hospital from MedicalRecord
    hospital_data = []
    for h in hospitals:
        expense = MedicalRecord.objects.filter(hospital__icontains=h.name).aggregate(total=Sum('total_expense'))['total'] or 0
        visit_count = MedicalRecord.objects.filter(hospital__icontains=h.name).count()
        hospital_data.append({'hospital': h, 'total_expense': expense, 'visit_count': visit_count})
    
    return render(request, 'welfare_app/reports/hospital.html', {
        'hospital_data': hospital_data, 'active_nav': 'reports',
    })


@login_required
def claim_report(request):
    claims = MedicalClaim.objects.select_related('employee', 'hospital').all()
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status:
        claims = claims.filter(claim_status=status)
    if date_from:
        claims = claims.filter(claim_date__gte=date_from)
    if date_to:
        claims = claims.filter(claim_date__lte=date_to)
    
    summary = claims.aggregate(
        total_billed=Sum('total_bill_amount'),
        total_approved=Sum('approved_amount'),
        total_rejected=Sum('rejected_amount'),
    )
    
    paginator = Paginator(claims.order_by('-claim_date'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'welfare_app/reports/claim.html', {
        'page_obj': page_obj, 'summary': summary, 'status': status,
        'date_from': date_from, 'date_to': date_to, 'active_nav': 'reports',
    })


@login_required
def budget_report(request):
    year = request.GET.get('year', timezone.now().year)
    budgets = Budget.objects.filter(year=year).select_related('department')
    return render(request, 'welfare_app/reports/budget.html', {
        'budgets': budgets, 'year': year, 'active_nav': 'reports',
    })


@login_required
def inventory_report(request):
    medicines = Medicine.objects.all()
    return render(request, 'welfare_app/reports/inventory.html', {
        'medicines': medicines, 'active_nav': 'reports',
    })


@login_required
def export_report(request, report_type):
    fmt = request.GET.get('format', 'csv')
    
    if report_type == 'employees':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employee_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['PL Number', 'Name', 'Department', 'Designation', 'Status', 'Contact', 'Email'])
        for emp in Employee.objects.all().order_by('name'):
            writer.writerow([emp.pl_number, emp.name, emp.department, emp.designation or '', 
                           emp.employment_status, emp.contact_number or '', emp.email or ''])
        return response
    
    elif report_type == 'expenses':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expense_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Employee', 'PL Number', 'Hospital', 'Doctor Fee', 'Lab Fee', 'Medicine', 'Admission', 'Other', 'Total', 'Status'])
        for rec in MedicalRecord.objects.select_related('employee').order_by('-treatment_date'):
            writer.writerow([rec.treatment_date, rec.employee.name, rec.employee.pl_number, rec.hospital,
                           rec.doctor_fee, rec.lab_fee, rec.medicine_fee, rec.admission_fee, rec.other_fee,
                           rec.total_expense, rec.status])
        return response
    
    elif report_type == 'claims':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="claim_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Claim #', 'Employee', 'Date', 'Total Bill', 'Approved', 'Status', 'Payment'])
        for c in MedicalClaim.objects.select_related('employee').order_by('-claim_date'):
            writer.writerow([c.claim_number, c.employee.name if c.employee else '', c.claim_date,
                           c.total_bill_amount, c.approved_amount, c.claim_status, c.payment_status])
        return response
    
    return redirect('report_index')

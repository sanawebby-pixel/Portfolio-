from collections import defaultdict

from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import EmployeeForm, MedicalRecordForm
from .models import Employee, MedicalRecord


def dashboard(request):
    employees = Employee.objects.all()
    records = MedicalRecord.objects.select_related('employee').all().order_by('-treatment_date')

    total_employees = employees.count()
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

    context = {
        'employees': employees,
        'records': records,
        'total_employees': total_employees,
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
    }
    return render(request, 'welfare_app/dashboard.html', context)


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


def edit_employee(request, pk):
    employee = Employee.objects.get(pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('dashboard'))
    return render(request, 'welfare_app/dashboard.html', {'employees': Employee.objects.all(), 'employee_form': EmployeeForm(instance=employee), 'record_form': MedicalRecordForm()})


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


def delete_record(request, pk):
    MedicalRecord.objects.filter(pk=pk).delete()
    return HttpResponseRedirect(reverse('dashboard'))


def delete_employee(request, pk):
    Employee.objects.filter(pk=pk).delete()
    return HttpResponseRedirect(reverse('dashboard'))

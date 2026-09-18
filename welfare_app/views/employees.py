from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from ..models import Employee, Dependent, HospitalVisit, MedicalClaim, MedicalRecord, Document, AuditLog
from ..forms.employee_forms import FullEmployeeForm, DependentForm


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    q = request.GET.get('q', '').strip()
    department = request.GET.get('department', '').strip()
    status = request.GET.get('status', '').strip()
    sort = request.GET.get('sort', 'name')
    
    if q:
        employees = employees.filter(
            Q(name__icontains=q) | Q(pl_number__icontains=q) | 
            Q(cnic__icontains=q) | Q(contact_number__icontains=q) |
            Q(designation__icontains=q)
        )
    if department:
        employees = employees.filter(department__iexact=department)
    if status:
        employees = employees.filter(employment_status=status)
    
    # Sorting
    valid_sorts = ['name', '-name', 'pl_number', '-pl_number', 'department', 'created_at', '-created_at', 'joined_date']
    if sort in valid_sorts:
        employees = employees.order_by(sort)
    else:
        employees = employees.order_by('name')
    
    # Unique departments for filter dropdown
    departments = Employee.objects.values_list('department', flat=True).distinct().order_by('department')
    
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'department': department,
        'status': status,
        'sort': sort,
        'departments': [d for d in departments if d],
        'active_nav': 'employees',
        'total_count': employees.count(),
    }
    return render(request, 'welfare_app/employees/list.html', context)


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    dependents = Dependent.objects.filter(employee=employee).order_by('-created_at')
    medical_records = MedicalRecord.objects.filter(employee=employee).order_by('-treatment_date')
    
    try:
        visits = HospitalVisit.objects.filter(employee=employee).select_related('hospital', 'doctor').order_by('-visit_date')
    except Exception:
        visits = []
        
    try:
        claims = MedicalClaim.objects.filter(employee=employee).select_related('hospital').order_by('-claim_date')
    except Exception:
        claims = []
        
    try:
        documents = Document.objects.filter(content_type_name='employee', object_id=employee.pk).order_by('-created_at')
    except Exception:
        documents = []
    
    total_expense = employee.total_medical_expense()
    total_visits = len(visits) if visits else medical_records.count()
    active_claims = MedicalClaim.objects.filter(employee=employee, claim_status__in=['Submitted', 'Under Review']).count() if MedicalClaim else 0
    
    context = {
        'employee': employee,
        'dependents': dependents,
        'medical_records': medical_records,
        'visits': visits,
        'claims': claims,
        'documents': documents,
        'total_expense': total_expense,
        'total_visits': total_visits,
        'active_claims': active_claims,
        'active_nav': 'employees',
    }
    return render(request, 'welfare_app/employees/detail.html', context)


@login_required
def employee_create(request):
    if request.method == 'POST':
        form = FullEmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            AuditLog.log(
                user=request.user, action='Created', module='Employee',
                record_id=str(employee.pk), record_repr=str(employee),
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Employee "{employee.name}" ({employee.pl_number}) created successfully.')
            return redirect('employee_detail', pk=employee.pk)
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        form = FullEmployeeForm()
    
    return render(request, 'welfare_app/employees/form.html', {
        'form': form,
        'active_nav': 'employees',
    })


@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = FullEmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save()
            AuditLog.log(
                user=request.user, action='Updated', module='Employee',
                record_id=str(employee.pk), record_repr=str(employee),
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Employee "{employee.name}" ({employee.pl_number}) updated successfully.')
            return redirect('employee_detail', pk=employee.pk)
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        form = FullEmployeeForm(instance=employee)
    
    return render(request, 'welfare_app/employees/form.html', {
        'form': form,
        'employee': employee,
        'active_nav': 'employees',
    })


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    emp_repr = f"{employee.name} ({employee.pl_number})"
    employee.delete()
    AuditLog.log(
        user=request.user, action='Deleted', module='Employee',
        record_id=str(pk), record_repr=emp_repr,
        ip_address=getattr(request, 'client_ip', None)
    )
    messages.success(request, f'Employee "{emp_repr}" has been deleted.')
    return redirect('employee_list')


@login_required
def dependent_create(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    if request.method == 'POST':
        form = DependentForm(request.POST)
        if form.is_valid():
            dependent = form.save(commit=False)
            dependent.employee = employee
            dependent.save()
            AuditLog.log(
                user=request.user, action='Created', module='Dependent',
                record_id=str(dependent.pk), record_repr=f"{dependent.name} ({employee.name})",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Family member "{dependent.name}" added for {employee.name}.')
            return redirect('employee_detail', pk=employee_pk)
        else:
            messages.error(request, 'Please correct the dependent details below.')
    else:
        form = DependentForm()
    
    return render(request, 'welfare_app/employees/dependent_form.html', {
        'form': form,
        'employee': employee,
        'active_nav': 'employees',
    })


@login_required
def dependent_update(request, pk):
    dependent = get_object_or_404(Dependent, pk=pk)
    employee = dependent.employee
    if request.method == 'POST':
        form = DependentForm(request.POST, instance=dependent)
        if form.is_valid():
            form.save()
            AuditLog.log(
                user=request.user, action='Updated', module='Dependent',
                record_id=str(dependent.pk), record_repr=f"{dependent.name} ({employee.name})",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Dependent "{dependent.name}" updated successfully.')
            return redirect('employee_detail', pk=employee.pk)
        else:
            messages.error(request, 'Please correct the dependent details below.')
    else:
        form = DependentForm(instance=dependent)
    
    return render(request, 'welfare_app/employees/dependent_form.html', {
        'form': form,
        'employee': employee,
        'dependent': dependent,
        'active_nav': 'employees',
    })


@login_required
def dependent_delete(request, pk):
    dependent = get_object_or_404(Dependent, pk=pk)
    employee_pk = dependent.employee.pk
    dep_name = dependent.name
    dependent.delete()
    AuditLog.log(
        user=request.user, action='Deleted', module='Dependent',
        record_id=str(pk), record_repr=f"{dep_name}",
        ip_address=getattr(request, 'client_ip', None)
    )
    messages.success(request, f'Dependent "{dep_name}" removed.')
    return redirect('employee_detail', pk=employee_pk)

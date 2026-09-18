from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from ..models import HospitalVisit, Employee, Dependent, Hospital, Doctor, MedicalClaim, AuditLog
from ..forms.visit_forms import HospitalVisitForm


@login_required
def visit_list(request):
    visits = HospitalVisit.objects.select_related('employee', 'hospital', 'doctor', 'dependent').all()

    q = request.GET.get('q', '').strip()
    visit_type = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()
    hospital_id = request.GET.get('hospital', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if q:
        visits = visits.filter(
            Q(employee__name__icontains=q) |
            Q(employee__pl_number__icontains=q) |
            Q(dependent__name__icontains=q) |
            Q(diagnosis__icontains=q) |
            Q(hospital__name__icontains=q) |
            Q(doctor__name__icontains=q) |
            Q(symptoms__icontains=q) |
            Q(treatment__icontains=q)
        )
    if visit_type:
        visits = visits.filter(visit_type=visit_type)
    if status:
        visits = visits.filter(status=status)
    if hospital_id:
        visits = visits.filter(hospital_id=hospital_id)
    if date_from:
        visits = visits.filter(visit_date__gte=date_from)
    if date_to:
        visits = visits.filter(visit_date__lte=date_to)

    # Summary Statistics Ribbon
    all_visits = HospitalVisit.objects.all()
    stats = {
        'total_count': all_visits.count(),
        'opd_count': all_visits.filter(visit_type='OPD').count(),
        'emergency_count': all_visits.filter(visit_type='Emergency').count(),
        'admission_count': all_visits.filter(visit_type='Admission').count(),
        'total_cost': all_visits.aggregate(s=Sum('total_visit_cost'))['s'] or 0,
    }

    hospitals = Hospital.objects.filter(status='Active').order_by('name')
    paginator = Paginator(visits.order_by('-visit_date', '-id'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'hospitals': hospitals,
        'q': q,
        'visit_type': visit_type,
        'status': status,
        'hospital_id': hospital_id,
        'date_from': date_from,
        'date_to': date_to,
        'active_nav': 'visits',
    }
    return render(request, 'welfare_app/visits/list.html', context)


@login_required
def visit_detail(request, pk):
    visit = get_object_or_404(
        HospitalVisit.objects.select_related('employee', 'hospital', 'doctor', 'dependent'),
        pk=pk
    )
    # Linked medical claims created from this visit
    claims = MedicalClaim.objects.filter(hospital_visit=visit).order_by('-claim_date')

    context = {
        'visit': visit,
        'claims': claims,
        'active_nav': 'visits',
    }
    return render(request, 'welfare_app/visits/detail.html', context)


@login_required
def visit_create(request):
    if request.method == 'POST':
        form = HospitalVisitForm(request.POST, request.FILES)
        if form.is_valid():
            visit = form.save()
            AuditLog.log(
                user=request.user, action='Created', module='HospitalVisit',
                record_id=str(visit.pk),
                record_repr=f'Visit ({visit.visit_type}) for {visit.employee.name} at {visit.hospital.name if visit.hospital else "General Clinic"}',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Hospital visit for "{visit.employee.name}" successfully recorded.')
            return redirect('visit_detail', pk=visit.pk)
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        initial_data = {'visit_date': timezone.now().date(), 'status': 'Completed'}
        emp_id = request.GET.get('employee')
        hosp_id = request.GET.get('hospital')
        if emp_id:
            initial_data['employee'] = emp_id
        if hosp_id:
            initial_data['hospital'] = hosp_id
        form = HospitalVisitForm(initial=initial_data)

    return render(request, 'welfare_app/visits/form.html', {
        'form': form,
        'title': 'Log Hospital Consultation / Visit',
        'active_nav': 'visits'
    })


@login_required
def visit_update(request, pk):
    visit = get_object_or_404(HospitalVisit, pk=pk)
    if request.method == 'POST':
        form = HospitalVisitForm(request.POST, request.FILES, instance=visit)
        if form.is_valid():
            visit = form.save()
            AuditLog.log(
                user=request.user, action='Updated', module='HospitalVisit',
                record_id=str(visit.pk),
                record_repr=f'Updated visit ({visit.visit_date}) for {visit.employee.name}',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Hospital visit record updated.')
            return redirect('visit_detail', pk=visit.pk)
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        form = HospitalVisitForm(instance=visit)

    return render(request, 'welfare_app/visits/form.html', {
        'form': form,
        'visit': visit,
        'title': f'Edit Hospital Visit Record - {visit.employee.name}',
        'active_nav': 'visits'
    })


@login_required
def visit_delete(request, pk):
    visit = get_object_or_404(HospitalVisit, pk=pk)
    v_repr = f'Visit for {visit.employee.name} ({visit.visit_date})'
    visit.delete()
    AuditLog.log(
        user=request.user, action='Deleted', module='HospitalVisit',
        record_id=str(pk), record_repr=v_repr,
        ip_address=getattr(request, 'client_ip', None)
    )
    messages.success(request, 'Hospital visit record deleted.')
    return redirect('visit_list')

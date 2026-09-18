from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from ..models import Hospital, Doctor, HospitalVisit, MedicalRecord, MedicalClaim, AuditLog
from ..forms.hospital_forms import HospitalForm


@login_required
def hospital_list(request):
    hospitals = Hospital.objects.all()
    q = request.GET.get('q', '')
    hospital_type = request.GET.get('type', '')
    panel = request.GET.get('panel', '')
    status = request.GET.get('status', '')
    
    if q:
        hospitals = hospitals.filter(Q(name__icontains=q) | Q(city__icontains=q))
    if hospital_type:
        hospitals = hospitals.filter(hospital_type=hospital_type)
    if panel:
        hospitals = hospitals.filter(panel_status=panel)
    if status:
        hospitals = hospitals.filter(status=status)
    
    paginator = Paginator(hospitals.order_by('name'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'hospital_type': hospital_type,
        'panel': panel,
        'status': status,
        'active_nav': 'hospitals',
        'total_count': hospitals.count(),
    }
    return render(request, 'welfare_app/hospitals/list.html', context)


@login_required
def hospital_detail(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    doctors = Doctor.objects.filter(hospital=hospital)
    visits = HospitalVisit.objects.filter(hospital=hospital).order_by('-visit_date')[:20]
    
    # Calculate total expenses for this hospital from MedicalRecord
    hospital_expenses = MedicalRecord.objects.filter(
        hospital__icontains=hospital.name
    ).aggregate(total=Sum('total_expense'))['total'] or 0
    
    # Claims related to this hospital
    claims = MedicalClaim.objects.filter(hospital=hospital).order_by('-claim_date')[:20]
    
    context = {
        'hospital': hospital,
        'doctors': doctors,
        'visits': visits,
        'claims': claims,
        'hospital_expenses': hospital_expenses,
        'active_nav': 'hospitals',
    }
    return render(request, 'welfare_app/hospitals/detail.html', context)


@login_required
def hospital_create(request):
    if request.method == 'POST':
        form = HospitalForm(request.POST)
        if form.is_valid():
            hospital = form.save()
            AuditLog.log(user=request.user, action='Created', module='Hospital',
                        record_id=str(hospital.pk), record_repr=str(hospital),
                        ip_address=getattr(request, 'client_ip', None))
            messages.success(request, f'Hospital {hospital.name} created.')
            return redirect('hospital_list')
    else:
        form = HospitalForm()
    return render(request, 'welfare_app/hospitals/form.html', {'form': form, 'active_nav': 'hospitals'})


@login_required
def hospital_update(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    if request.method == 'POST':
        form = HospitalForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            AuditLog.log(user=request.user, action='Updated', module='Hospital',
                        record_id=str(hospital.pk), record_repr=str(hospital),
                        ip_address=getattr(request, 'client_ip', None))
            messages.success(request, f'Hospital {hospital.name} updated.')
            return redirect('hospital_detail', pk=hospital.pk)
    else:
        form = HospitalForm(instance=hospital)
    return render(request, 'welfare_app/hospitals/form.html', {'form': form, 'hospital': hospital, 'active_nav': 'hospitals'})


@login_required
def hospital_delete(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    if request.method == 'POST':
        hospital.delete()
        messages.success(request, 'Hospital deleted.')
    return redirect('hospital_list')

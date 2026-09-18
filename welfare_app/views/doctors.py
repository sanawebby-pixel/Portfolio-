from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from ..models import Doctor, Hospital, AuditLog
from ..forms.hospital_forms import DoctorForm


@login_required
def doctor_list(request):
    doctors = Doctor.objects.select_related('hospital').annotate(
        visits_count=Count('visits', distinct=True),
        claims_count=Count('medical_claims', distinct=True)
    ).all()

    q = request.GET.get('q', '').strip()
    hospital_id = request.GET.get('hospital', '').strip()
    specialization = request.GET.get('specialization', '').strip()
    status = request.GET.get('status', '').strip()

    if q:
        doctors = doctors.filter(
            Q(name__icontains=q) |
            Q(specialization__icontains=q) |
            Q(registration_number__icontains=q) |
            Q(hospital__name__icontains=q) |
            Q(contact__icontains=q)
        )
    if hospital_id:
        doctors = doctors.filter(hospital_id=hospital_id)
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)
    if status:
        doctors = doctors.filter(status=status)

    # Statistics Ribbon
    all_doctors = Doctor.objects.all()
    stats = {
        'total_count': all_doctors.count(),
        'active_count': all_doctors.filter(status='Active').count(),
        'hospitals_count': Hospital.objects.filter(status='Active').count(),
        'avg_fee': all_doctors.aggregate(a=Avg('consultation_fee'))['a'] or 0,
    }

    hospitals = Hospital.objects.filter(status='Active').order_by('name')
    specializations = Doctor.objects.exclude(specialization__isnull=True).exclude(specialization__exact='').values_list('specialization', flat=True).distinct().order_by('specialization')

    paginator = Paginator(doctors.order_by('name'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'q': q,
        'hospital_id': hospital_id,
        'specialization': specialization,
        'status': status,
        'hospitals': hospitals,
        'specializations': specializations,
        'active_nav': 'doctors',
    }
    return render(request, 'welfare_app/doctors/list.html', context)


@login_required
def doctor_create(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            AuditLog.log(
                user=request.user, action='Created', module='Doctor',
                record_id=str(doctor.pk), record_repr=f'{doctor.name} ({doctor.specialization})',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Doctor "{doctor.name}" added successfully.')
            return redirect('doctor_list')
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        # Pre-select hospital if passed in query param
        hosp_id = request.GET.get('hospital')
        initial_data = {'hospital': hosp_id} if hosp_id else {}
        form = DoctorForm(initial=initial_data)

    return render(request, 'welfare_app/doctors/form.html', {
        'form': form,
        'title': 'Register Specialist / Doctor',
        'active_nav': 'doctors'
    })


@login_required
def doctor_update(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            doctor = form.save()
            AuditLog.log(
                user=request.user, action='Updated', module='Doctor',
                record_id=str(doctor.pk), record_repr=f'{doctor.name} ({doctor.specialization})',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Doctor "{doctor.name}" profile updated.')
            return redirect('doctor_list')
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        form = DoctorForm(instance=doctor)

    return render(request, 'welfare_app/doctors/form.html', {
        'form': form,
        'doctor': doctor,
        'title': f'Edit Profile - {doctor.name}',
        'active_nav': 'doctors'
    })


@login_required
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    doc_name = doctor.name
    doctor.delete()
    AuditLog.log(
        user=request.user, action='Deleted', module='Doctor',
        record_id=str(pk), record_repr=doc_name,
        ip_address=getattr(request, 'client_ip', None)
    )
    messages.success(request, f'Doctor "{doc_name}" removed from registry.')
    return redirect('doctor_list')

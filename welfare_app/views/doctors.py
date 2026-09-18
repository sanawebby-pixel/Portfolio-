from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import Doctor, Hospital, AuditLog
from ..forms.hospital_forms import DoctorForm


@login_required
def doctor_list(request):
    doctors = Doctor.objects.select_related('hospital').all()
    q = request.GET.get('q', '')
    hospital_id = request.GET.get('hospital', '')
    specialization = request.GET.get('specialization', '')
    
    if q:
        doctors = doctors.filter(Q(name__icontains=q) | Q(specialization__icontains=q))
    if hospital_id:
        doctors = doctors.filter(hospital_id=hospital_id)
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)
    
    hospitals = Hospital.objects.filter(status='Active').order_by('name')
    specializations = Doctor.objects.values_list('specialization', flat=True).distinct().order_by('specialization')
    
    paginator = Paginator(doctors.order_by('name'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'hospital_id': hospital_id,
        'specialization': specialization,
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
            messages.success(request, f'Doctor {doctor.name} added.')
            return redirect('doctor_list')
    else:
        form = DoctorForm()
    return render(request, 'welfare_app/doctors/form.html', {'form': form, 'active_nav': 'doctors'})


@login_required
def doctor_update(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Doctor {doctor.name} updated.')
            return redirect('doctor_list')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'welfare_app/doctors/form.html', {'form': form, 'doctor': doctor, 'active_nav': 'doctors'})


@login_required
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        doctor.delete()
        messages.success(request, 'Doctor removed.')
    return redirect('doctor_list')

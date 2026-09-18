from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from ..models import Hospital, Doctor, HospitalVisit, MedicalRecord, MedicalClaim, AuditLog
from ..forms.hospital_forms import HospitalForm


@login_required
def hospital_list(request):
    hospitals = Hospital.objects.annotate(
        doctors_count=Count('doctors', distinct=True),
        visits_count=Count('visits', distinct=True),
        claims_count=Count('medical_claims', distinct=True)
    ).all()

    q = request.GET.get('q', '').strip()
    hospital_type = request.GET.get('type', '').strip()
    panel = request.GET.get('panel', '').strip()
    status = request.GET.get('status', '').strip()
    city = request.GET.get('city', '').strip()

    if q:
        hospitals = hospitals.filter(
            Q(name__icontains=q) |
            Q(hospital_code__icontains=q) |
            Q(city__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(contact_number__icontains=q)
        )
    if hospital_type:
        hospitals = hospitals.filter(hospital_type=hospital_type)
    if panel:
        hospitals = hospitals.filter(panel_status=panel)
    if status:
        hospitals = hospitals.filter(status=status)
    if city:
        hospitals = hospitals.filter(city__iexact=city)

    # Statistics Ribbon
    all_hospitals = Hospital.objects.all()
    today = timezone.now().date()
    stats = {
        'total_count': all_hospitals.count(),
        'panel_count': all_hospitals.filter(panel_status='Panel').count(),
        'active_count': all_hospitals.filter(status='Active').count(),
        'total_doctors': Doctor.objects.count(),
        'total_claims_amount': MedicalClaim.objects.aggregate(s=Sum('total_bill_amount'))['s'] or 0,
    }

    # Unique Cities for filter
    cities = Hospital.objects.exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True).distinct().order_by('city')

    paginator = Paginator(hospitals.order_by('name'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'cities': cities,
        'q': q,
        'hospital_type': hospital_type,
        'panel': panel,
        'status': status,
        'city': city,
        'active_nav': 'hospitals',
    }
    return render(request, 'welfare_app/hospitals/list.html', context)


@login_required
def hospital_detail(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    doctors = Doctor.objects.filter(hospital=hospital).order_by('name')
    visits = HospitalVisit.objects.filter(hospital=hospital).select_related('employee', 'doctor', 'dependent').order_by('-visit_date')[:15]
    claims = MedicalClaim.objects.filter(hospital=hospital).select_related('employee', 'doctor').order_by('-claim_date')[:15]

    # Calculate financial aggregates for this facility
    total_claims_amount = MedicalClaim.objects.filter(hospital=hospital).aggregate(s=Sum('total_bill_amount'))['s'] or 0
    approved_claims_amount = MedicalClaim.objects.filter(hospital=hospital, claim_status__in=['Approved', 'Partially Approved', 'Paid']).aggregate(s=Sum('approved_amount'))['s'] or 0
    total_visits_count = HospitalVisit.objects.filter(hospital=hospital).count()

    # Legacy records fallback
    if total_claims_amount == 0:
        legacy_exp = MedicalRecord.objects.filter(hospital__icontains=hospital.name).aggregate(s=Sum('total_expense'))['s'] or 0
        total_claims_amount = legacy_exp
        approved_claims_amount = legacy_exp

    context = {
        'hospital': hospital,
        'doctors': doctors,
        'visits': visits,
        'claims': claims,
        'total_claims_amount': total_claims_amount,
        'approved_claims_amount': approved_claims_amount,
        'total_visits_count': total_visits_count,
        'active_nav': 'hospitals',
    }
    return render(request, 'welfare_app/hospitals/detail.html', context)


@login_required
def hospital_create(request):
    if request.method == 'POST':
        form = HospitalForm(request.POST)
        if form.is_valid():
            hospital = form.save()
            AuditLog.log(
                user=request.user, action='Created', module='Hospital',
                record_id=str(hospital.pk), record_repr=f'{hospital.name} ({hospital.hospital_code})',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Hospital "{hospital.name}" successfully registered.')
            return redirect('hospital_detail', pk=hospital.pk)
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        form = HospitalForm()

    return render(request, 'welfare_app/hospitals/form.html', {
        'form': form,
        'title': 'Register New Hospital / Clinic',
        'active_nav': 'hospitals'
    })


@login_required
def hospital_update(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    if request.method == 'POST':
        form = HospitalForm(request.POST, instance=hospital)
        if form.is_valid():
            hospital = form.save()
            AuditLog.log(
                user=request.user, action='Updated', module='Hospital',
                record_id=str(hospital.pk), record_repr=f'{hospital.name} ({hospital.hospital_code})',
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f'Hospital "{hospital.name}" updated successfully.')
            return redirect('hospital_detail', pk=hospital.pk)
        else:
            messages.error(request, 'Please check the form for errors and try again.')
    else:
        form = HospitalForm(instance=hospital)

    return render(request, 'welfare_app/hospitals/form.html', {
        'form': form,
        'hospital': hospital,
        'title': f'Edit Hospital - {hospital.name}',
        'active_nav': 'hospitals'
    })


@login_required
def hospital_delete(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    h_name = hospital.name
    hospital.delete()
    AuditLog.log(
        user=request.user, action='Deleted', module='Hospital',
        record_id=str(pk), record_repr=h_name,
        ip_address=getattr(request, 'client_ip', None)
    )
    messages.success(request, f'Hospital "{h_name}" was successfully deleted.')
    return redirect('hospital_list')

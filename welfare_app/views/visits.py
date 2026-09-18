from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import HospitalVisit, Employee, Hospital, Doctor, AuditLog
from ..forms.visit_forms import HospitalVisitForm


@login_required
def visit_list(request):
    visits = HospitalVisit.objects.select_related('employee', 'hospital', 'doctor').all()
    q = request.GET.get('q', '')
    visit_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if q:
        visits = visits.filter(
            Q(employee__name__icontains=q) | Q(diagnosis__icontains=q) |
            Q(employee__pl_number__icontains=q)
        )
    if visit_type:
        visits = visits.filter(visit_type=visit_type)
    if status:
        visits = visits.filter(status=status)
    if date_from:
        visits = visits.filter(visit_date__gte=date_from)
    if date_to:
        visits = visits.filter(visit_date__lte=date_to)
    
    paginator = Paginator(visits.order_by('-visit_date'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'visit_type': visit_type,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'active_nav': 'visits',
    }
    return render(request, 'welfare_app/visits/list.html', context)


@login_required
def visit_detail(request, pk):
    visit = get_object_or_404(HospitalVisit.objects.select_related('employee', 'hospital', 'doctor', 'dependent'), pk=pk)
    return render(request, 'welfare_app/visits/detail.html', {'visit': visit, 'active_nav': 'visits'})


@login_required
def visit_create(request):
    if request.method == 'POST':
        form = HospitalVisitForm(request.POST)
        if form.is_valid():
            visit = form.save()
            AuditLog.log(user=request.user, action='Created', module='HospitalVisit',
                        record_id=str(visit.pk), record_repr=str(visit),
                        ip_address=getattr(request, 'client_ip', None))
            messages.success(request, 'Hospital visit recorded.')
            return redirect('visit_detail', pk=visit.pk)
    else:
        form = HospitalVisitForm()
    return render(request, 'welfare_app/visits/form.html', {'form': form, 'active_nav': 'visits'})


@login_required
def visit_update(request, pk):
    visit = get_object_or_404(HospitalVisit, pk=pk)
    if request.method == 'POST':
        form = HospitalVisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Visit updated.')
            return redirect('visit_detail', pk=visit.pk)
    else:
        form = HospitalVisitForm(instance=visit)
    return render(request, 'welfare_app/visits/form.html', {'form': form, 'visit': visit, 'active_nav': 'visits'})


@login_required
def visit_delete(request, pk):
    visit = get_object_or_404(HospitalVisit, pk=pk)
    if request.method == 'POST':
        visit.delete()
        messages.success(request, 'Visit deleted.')
    return redirect('visit_list')

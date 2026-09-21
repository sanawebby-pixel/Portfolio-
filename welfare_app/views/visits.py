from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from ..models import HospitalVisit, Employee, Dependent, Hospital, Doctor, MedicalClaim, AuditLog, VisitExpenseItem
from ..forms.visit_forms import HospitalVisitForm


def save_visit_expense_items(visit, request):
    row_indices = request.POST.getlist('expense_row_index')
    if not row_indices:
        return

    retained_ids = []
    total_dynamic_cost = Decimal('0.00')

    for idx in row_indices:
        title = request.POST.get(f'expense_title_{idx}', '').strip()
        cost_str = request.POST.get(f'expense_cost_{idx}', '0').replace(',', '').strip()
        doc_file = request.FILES.get(f'expense_doc_{idx}')
        existing_id = request.POST.get(f'expense_existing_id_{idx}')

        try:
            cost_dec = Decimal(cost_str) if cost_str else Decimal('0.00')
        except (InvalidOperation, ValueError):
            cost_dec = Decimal('0.00')

        # If row is totally blank and has no file and no existing id, skip it
        if not title and cost_dec == 0 and not doc_file and not existing_id:
            continue

        item_title = title if title else 'Medical Expense'
        total_dynamic_cost += cost_dec

        if existing_id:
            item = VisitExpenseItem.objects.filter(pk=existing_id, visit=visit).first()
            if item:
                item.title = item_title
                item.cost = cost_dec
                if doc_file:
                    item.document = doc_file
                item.save()
                retained_ids.append(item.pk)
        else:
            item = VisitExpenseItem.objects.create(
                visit=visit,
                title=item_title,
                cost=cost_dec,
                document=doc_file
            )
            retained_ids.append(item.pk)

    # Delete any existing expense items that were deleted/removed by the user in edit mode
    visit.expense_items.exclude(pk__in=retained_ids).delete()

    # Update visit.total_visit_cost to match the dynamic rows sum
    if retained_ids:
        visit.total_visit_cost = total_dynamic_cost
        visit.save(update_fields=['total_visit_cost'])



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
            save_visit_expense_items(visit, request)
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
            save_visit_expense_items(visit, request)
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
        'existing_expenses': visit.expense_items.all(),
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

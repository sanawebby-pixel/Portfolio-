from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import Employee, Hospital, Doctor, MedicalClaim, Bill, Medicine, Supplier


@login_required
def global_search(request):
    q = request.GET.get('q', '').strip()
    results = {}
    
    if q and len(q) >= 2:
        results['employees'] = Employee.objects.filter(
            Q(name__icontains=q) | Q(pl_number__icontains=q) | Q(cnic__icontains=q)
        )[:5]
        results['hospitals'] = Hospital.objects.filter(
            Q(name__icontains=q) | Q(city__icontains=q)
        )[:5]
        results['doctors'] = Doctor.objects.filter(
            Q(name__icontains=q) | Q(specialization__icontains=q)
        )[:5]
        results['claims'] = MedicalClaim.objects.filter(
            Q(claim_number__icontains=q) | Q(employee__name__icontains=q)
        ).select_related('employee')[:5]
        results['bills'] = Bill.objects.filter(
            Q(bill_number__icontains=q) | Q(vendor_name__icontains=q)
        )[:5]
        results['medicines'] = Medicine.objects.filter(
            Q(name__icontains=q) | Q(generic_name__icontains=q)
        )[:5]
        results['suppliers'] = Supplier.objects.filter(
            Q(name__icontains=q) | Q(contact_person__icontains=q)
        )[:5]
    
    total_results = sum(len(v) for v in results.values())
    
    return render(request, 'welfare_app/search/results.html', {
        'q': q, 'results': results, 'total_results': total_results,
    })

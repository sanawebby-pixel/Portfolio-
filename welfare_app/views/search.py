from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import (
    Employee, Hospital, Doctor, MedicalClaim, HospitalVisit,
    Bill, Medicine, Supplier, PurchaseRequest, PurchaseOrder, Budget
)


@login_required
def global_search(request):
    """Global ERP Multi-entity Search Engine across all operational records."""
    q = request.GET.get('q', '').strip()
    tab = request.GET.get('tab', 'all').strip()

    results = {
        'employees': [],
        'claims': [],
        'hospitals': [],
        'doctors': [],
        'visits': [],
        'bills': [],
        'medicines': [],
        'suppliers': [],
        'purchase_orders': [],
        'budgets': [],
    }
    counts = {k: 0 for k in results}

    if q and len(q) >= 2:
        # 1. Employees
        emp_qs = Employee.objects.filter(
            Q(name__icontains=q) |
            Q(pl_number__icontains=q) |
            Q(cnic__icontains=q) |
            Q(department__icontains=q) |
            Q(designation__icontains=q) |
            Q(contact_number__icontains=q)
        )
        counts['employees'] = emp_qs.count()
        results['employees'] = emp_qs[:10]

        # 2. Medical Claims
        claim_qs = MedicalClaim.objects.select_related('employee', 'hospital').filter(
            Q(claim_number__icontains=q) |
            Q(bill_number__icontains=q) |
            Q(diagnosis__icontains=q) |
            Q(employee__name__icontains=q) |
            Q(employee__pl_number__icontains=q)
        )
        counts['claims'] = claim_qs.count()
        results['claims'] = claim_qs[:10]

        # 3. Hospitals
        hosp_qs = Hospital.objects.filter(
            Q(name__icontains=q) |
            Q(hospital_code__icontains=q) |
            Q(city__icontains=q) |
            Q(contact_person__icontains=q)
        )
        counts['hospitals'] = hosp_qs.count()
        results['hospitals'] = hosp_qs[:10]

        # 4. Doctors
        doc_qs = Doctor.objects.select_related('hospital').filter(
            Q(name__icontains=q) |
            Q(specialization__icontains=q) |
            Q(hospital__name__icontains=q)
        )
        counts['doctors'] = doc_qs.count()
        results['doctors'] = doc_qs[:10]

        # 5. Hospital Visits
        visit_qs = HospitalVisit.objects.select_related('employee', 'hospital', 'doctor').filter(
            Q(diagnosis__icontains=q) |
            Q(employee__name__icontains=q) |
            Q(hospital_name__icontains=q) |
            Q(doctor_name__icontains=q)
        )
        counts['visits'] = visit_qs.count()
        results['visits'] = visit_qs[:10]

        # 6. Bills & Invoices
        bill_qs = Bill.objects.select_related('hospital', 'employee').filter(
            Q(bill_number__icontains=q) |
            Q(vendor_name__icontains=q) |
            Q(description__icontains=q)
        )
        counts['bills'] = bill_qs.count()
        results['bills'] = bill_qs[:10]

        # 7. Pharmacy Medicines
        med_qs = Medicine.objects.select_related('supplier').filter(
            Q(name__icontains=q) |
            Q(generic_name__icontains=q) |
            Q(batch_number__icontains=q) |
            Q(manufacturer__icontains=q) |
            Q(medicine_id__icontains=q)
        )
        counts['medicines'] = med_qs.count()
        results['medicines'] = med_qs[:10]

        # 8. Suppliers
        sup_qs = Supplier.objects.filter(
            Q(name__icontains=q) |
            Q(supplier_id__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(city__icontains=q)
        )
        counts['suppliers'] = sup_qs.count()
        results['suppliers'] = sup_qs[:10]

        # 9. Purchase Orders
        po_qs = PurchaseOrder.objects.select_related('supplier').filter(
            Q(order_number__icontains=q) |
            Q(supplier__name__icontains=q) |
            Q(items_description__icontains=q)
        )
        counts['purchase_orders'] = po_qs.count()
        results['purchase_orders'] = po_qs[:10]

        # 10. Budgets
        budget_qs = Budget.objects.select_related('department').filter(
            Q(department__name__icontains=q) |
            Q(category__icontains=q)
        )
        counts['budgets'] = budget_qs.count()
        results['budgets'] = budget_qs[:10]

    total_results = sum(counts.values())

    return render(request, 'welfare_app/search/results.html', {
        'q': q,
        'tab': tab,
        'results': results,
        'counts': counts,
        'total_results': total_results,
        'active_nav': 'search',
    })

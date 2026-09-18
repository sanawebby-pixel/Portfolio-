from django.utils.crypto import get_random_string

def generate_claim_number():
    from ..models import MedicalClaim
    last_claim = MedicalClaim.objects.all().order_by('id').last()
    if not last_claim:
        return 'CLM-0001'
    claim_no = last_claim.claim_number
    if claim_no and claim_no.startswith('CLM-'):
        try:
            claim_int = int(claim_no.split('-')[1])
            new_claim_int = claim_int + 1
            return f'CLM-{new_claim_int:04d}'
        except Exception:
            pass
    return f'CLM-{get_random_string(4, "0123456789")}'

def generate_pr_number():
    from ..models import PurchaseRequest
    last_pr = PurchaseRequest.objects.all().order_by('id').last()
    if not last_pr:
        return 'PR-0001'
    pr_no = last_pr.pr_number
    if pr_no and pr_no.startswith('PR-'):
        try:
            pr_int = int(pr_no.split('-')[1])
            new_pr_int = pr_int + 1
            return f'PR-{new_pr_int:04d}'
        except Exception:
            pass
    return f'PR-{get_random_string(4, "0123456789")}'

def generate_po_number():
    from ..models import PurchaseOrder
    last_po = PurchaseOrder.objects.all().order_by('id').last()
    if not last_po:
        return 'PO-0001'
    po_no = last_po.po_number
    if po_no and po_no.startswith('PO-'):
        try:
            po_int = int(po_no.split('-')[1])
            new_po_int = po_int + 1
            return f'PO-{new_po_int:04d}'
        except Exception:
            pass
    return f'PO-{get_random_string(4, "0123456789")}'

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_audit(request, action, module, record_id='', record_repr='', old_values=None, new_values=None):
    from ..models import AuditLog
    if request and request.user.is_authenticated:
        ip_address = getattr(request, 'client_ip', get_client_ip(request))
        description = f"{action} performed in {module}"
        if record_repr:
            description += f" on {record_repr}"
        AuditLog.objects.create(
            user=request.user,
            action=action,
            module=module,
            record_id=str(record_id),
            record_repr=str(record_repr),
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            description=description
        )

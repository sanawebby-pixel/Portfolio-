from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from ..models import AuditLog


def is_admin_or_superuser(user):
    """Check if current user is admin or superuser."""
    if user.is_superuser:
        return True
    try:
        return user.profile.is_admin
    except Exception:
        return False


@login_required
def audit_log(request):
    """Centralized Audit Log & Security Trail Viewer."""
    if not is_admin_or_superuser(request.user):
        messages.error(request, "Access restricted: Audit Log inspection requires Administrator privileges.")
        return redirect('dashboard')

    logs = AuditLog.objects.select_related('user').all()

    q = request.GET.get('q', '').strip()
    module = request.GET.get('module', '').strip()
    action = request.GET.get('action', '').strip()
    user_id = request.GET.get('user', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if q:
        logs = logs.filter(
            Q(record_repr__icontains=q) |
            Q(module__icontains=q) |
            Q(user__username__icontains=q) |
            Q(ip_address__icontains=q)
        )
    if module:
        logs = logs.filter(module__iexact=module)
    if action:
        logs = logs.filter(action=action)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    total_logs_count = logs.count()
    users = User.objects.all().order_by('username')
    modules = AuditLog.objects.exclude(module__isnull=True).exclude(module='').values_list('module', flat=True).distinct().order_by('module')
    actions = [a[0] for a in AuditLog.ACTION_CHOICES]

    # Quick metrics
    created_count = AuditLog.objects.filter(action='Created').count()
    updated_count = AuditLog.objects.filter(action='Updated').count()
    deleted_count = AuditLog.objects.filter(action='Deleted').count()
    approved_count = AuditLog.objects.filter(action__in=['Approved', 'Paid']).count()

    paginator = Paginator(logs.order_by('-timestamp'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/audit/log.html', {
        'page_obj': page_obj,
        'q': q,
        'module': module,
        'action_filter': action,
        'user_id': user_id,
        'date_from': date_from,
        'date_to': date_to,
        'users': users,
        'modules': modules,
        'actions': actions,
        'total_logs_count': total_logs_count,
        'created_count': created_count,
        'updated_count': updated_count,
        'deleted_count': deleted_count,
        'approved_count': approved_count,
        'active_nav': 'audit',
    })

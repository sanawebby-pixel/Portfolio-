from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import AuditLog


@login_required
def audit_log(request):
    if not request.user.is_superuser:
        try:
            if request.user.profile.role != 'Admin':
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        except Exception:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    
    logs = AuditLog.objects.select_related('user').all()
    module = request.GET.get('module', '')
    action = request.GET.get('action', '')
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if module:
        logs = logs.filter(module__icontains=module)
    if action:
        logs = logs.filter(action=action)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    users = User.objects.all().order_by('username')
    modules = AuditLog.objects.values_list('module', flat=True).distinct()
    actions = AuditLog.objects.values_list('action', flat=True).distinct()
    
    paginator = Paginator(logs.order_by('-timestamp'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'welfare_app/audit/log.html', {
        'page_obj': page_obj, 'module': module, 'action_filter': action, 'user_id': user_id,
        'date_from': date_from, 'date_to': date_to,
        'users': users, 'modules': modules, 'actions': actions,
        'active_nav': 'audit',
    })

from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from functools import wraps
from .models import AuditLog
from .utils.helpers import get_client_ip

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                user_role = request.user.profile.role
            except Exception:
                user_role = 'Employee'
            
            if user_role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to view this page.")
        return _wrapped_view
    return decorator

def audit_action(action, module):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            if request.user.is_authenticated and response.status_code < 400:
                ip_address = getattr(request, 'client_ip', get_client_ip(request))
                AuditLog.objects.create(
                    user=request.user,
                    action=action,
                    module=module,
                    ip_address=ip_address,
                    description=f"{action} performed in {module}"
                )
            return response
        return _wrapped_view
    return decorator

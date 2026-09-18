from .models import Notification

def welfare_context(request):
    """Global context processor for all templates."""
    context = {
        'app_name': 'Welfare ERP',
        'app_subtitle': 'Hospital Management System',
    }
    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        try:
            context['user_profile'] = request.user.profile
            context['user_role'] = request.user.profile.role
        except Exception:
            context['user_profile'] = None
            context['user_role'] = 'Admin' if request.user.is_superuser else 'Employee'
    return context

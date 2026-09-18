from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render
from ..models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(notifications, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'welfare_app/notifications/list.html', {
        'page_obj': page_obj, 'unread_count': unread_count, 'active_nav': 'notifications',
    })


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    if notification.related_url:
        return redirect(notification.related_url)
    return redirect('notification_list')


@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')

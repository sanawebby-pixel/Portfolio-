from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Notification


@login_required
def notification_list(request):
    """List system notifications for current user with type filters and batch actions."""
    type_filter = request.GET.get('type', '').strip()
    status_filter = request.GET.get('status', '').strip()

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    total_count = notifications.count()
    unread_count = notifications.filter(is_read=False).count()
    read_count = total_count - unread_count

    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)
    if status_filter == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status_filter == 'read':
        notifications = notifications.filter(is_read=True)

    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    types = [t[0] for t in Notification.TYPE_CHOICES]

    return render(request, 'welfare_app/notifications/list.html', {
        'page_obj': page_obj,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'types': types,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
        'active_nav': 'notifications',
    })


@login_required
def notification_mark_read(request, pk):
    """Mark a single notification as read and optionally navigate to related URL."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()

    if notification.related_url:
        return redirect(notification.related_url)
    return redirect('notification_list')


@login_required
def notification_mark_all_read(request):
    """Mark all unread notifications as read for current user."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All unread notifications have been marked as read.")
    return redirect('notification_list')


@login_required
def notification_delete(request, pk):
    """Delete a notification."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, "Notification removed.")
    return redirect('notification_list')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import UserProfile, AuditLog
from ..forms.user_forms import UserCreateForm, UserUpdateForm, AdminPasswordChangeForm, ROLE_CHOICES


def is_admin_or_superuser(user):
    """Check if current user is admin or superuser."""
    if user.is_superuser:
        return True
    try:
        return user.profile.is_admin
    except Exception:
        return False


@login_required
def user_list(request):
    """List system user accounts with role filters, status badges, and management options."""
    if not is_admin_or_superuser(request.user):
        messages.error(request, "Access restricted: User administration requires Administrator privileges.")
        return redirect('dashboard')

    q = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()

    users = User.objects.all().select_related('profile', 'profile__department', 'profile__employee').order_by('-date_joined')

    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )
    if role_filter:
        users = users.filter(profile__role=role_filter)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(Q(is_superuser=True) | Q(profile__role='Admin')).distinct().count()
    officer_users = User.objects.filter(profile__role__in=['Welfare Officer', 'HR Staff', 'Finance Officer']).count()

    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'welfare_app/users/list.html', {
        'page_obj': page_obj,
        'q': q,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': ROLE_CHOICES,
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'officer_users': officer_users,
        'active_nav': 'users',
    })


@login_required
def user_create(request):
    """Create a new ERP user account with role permissions."""
    if not is_admin_or_superuser(request.user):
        messages.error(request, "Access restricted: User administration requires Administrator privileges.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role', 'Welfare Officer')
            department = form.cleaned_data.get('department')
            employee = form.cleaned_data.get('employee')
            phone = form.cleaned_data.get('phone', '')

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.department = department
            profile.employee = employee
            profile.phone = phone
            profile.save()

            AuditLog.log(
                user=request.user,
                action='Created',
                module='User',
                record_id=str(user.pk),
                record_repr=f"User: {user.username} ({role})",
                new_values={'username': user.username, 'email': user.email, 'role': role},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"User account for '{user.get_full_name() or user.username}' was successfully created with role '{role}'.")
            return redirect('user_list')
    else:
        form = UserCreateForm()

    return render(request, 'welfare_app/users/form.html', {
        'form': form,
        'is_edit': False,
        'active_nav': 'users',
    })


@login_required
def user_update(request, pk):
    """Update an existing user account and profile settings."""
    if not is_admin_or_superuser(request.user):
        messages.error(request, "Access restricted: User administration requires Administrator privileges.")
        return redirect('dashboard')

    user_obj = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            role = form.cleaned_data.get('role', profile.role)
            department = form.cleaned_data.get('department')
            employee = form.cleaned_data.get('employee')
            phone = form.cleaned_data.get('phone', '')

            profile.role = role
            profile.department = department
            profile.employee = employee
            profile.phone = phone
            profile.save()

            AuditLog.log(
                user=request.user,
                action='Updated',
                module='User',
                record_id=str(user_obj.pk),
                record_repr=f"Updated User: {user_obj.username}",
                new_values={'username': user_obj.username, 'role': role, 'is_active': user_obj.is_active},
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"User account '{user_obj.username}' was updated successfully.")
            return redirect('user_list')
    else:
        form = UserUpdateForm(
            instance=user_obj,
            initial={
                'role': profile.role,
                'department': profile.department,
                'employee': profile.employee,
                'phone': profile.phone,
            }
        )

    return render(request, 'welfare_app/users/form.html', {
        'form': form,
        'edit_user': user_obj,
        'profile': profile,
        'is_edit': True,
        'active_nav': 'users',
    })


@login_required
def user_toggle_active(request, pk):
    """Toggle active/inactive status for a user."""
    if not is_admin_or_superuser(request.user):
        messages.error(request, "Access restricted.")
        return redirect('dashboard')

    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "You cannot deactivate your own current logged-in account.")
        return redirect('user_list')

    user_obj.is_active = not user_obj.is_active
    user_obj.save()

    status_str = "activated" if user_obj.is_active else "deactivated"
    AuditLog.log(
        user=request.user,
        action='Updated',
        module='User',
        record_id=str(user_obj.pk),
        record_repr=f"User {user_obj.username} status changed to {status_str}",
        ip_address=getattr(request, 'client_ip', None)
    )
    messages.success(request, f"User '{user_obj.username}' has been {status_str}.")
    return redirect('user_list')


@login_required
def user_delete(request, pk):
    """Delete a user account."""
    if not is_admin_or_superuser(request.user):
        messages.error(request, "Access restricted.")
        return redirect('dashboard')

    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')

    username = user_obj.username
    if request.method == 'POST':
        user_obj.delete()
        AuditLog.log(
            user=request.user,
            action='Deleted',
            module='User',
            record_id=str(pk),
            record_repr=f"Deleted User: {username}",
            ip_address=getattr(request, 'client_ip', None)
        )
        messages.success(request, f"User account '{username}' was permanently deleted.")
        return redirect('user_list')

    return render(request, 'welfare_app/components/confirm_delete.html', {
        'object_name': f"User Account: {username}",
        'cancel_url': 'user_list',
        'active_nav': 'users',
    })


@login_required
def user_change_password(request, pk):
    """Administrative password reset tool for a specific user."""
    if not is_admin_or_superuser(request.user):
        messages.error(request, "Access restricted.")
        return redirect('dashboard')

    user_obj = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = AdminPasswordChangeForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user_obj.set_password(new_password)
            user_obj.save()
            AuditLog.log(
                user=request.user,
                action='Updated',
                module='User',
                record_id=str(user_obj.pk),
                record_repr=f"Password reset for user {user_obj.username}",
                ip_address=getattr(request, 'client_ip', None)
            )
            messages.success(request, f"Password for user '{user_obj.username}' has been successfully changed.")
            return redirect('user_list')
    else:
        form = AdminPasswordChangeForm()

    return render(request, 'welfare_app/users/password_form.html', {
        'form': form,
        'target_user': user_obj,
        'active_nav': 'users',
    })

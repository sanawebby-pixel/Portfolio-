from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import UserProfile, AuditLog
from ..forms.user_forms import UserCreateForm, UserUpdateForm


@login_required
def user_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    users = User.objects.all().select_related('profile').order_by('username')
    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'welfare_app/users/list.html', {
        'page_obj': page_obj, 'active_nav': 'users',
    })


@login_required
def user_create(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Update or create profile
            role = form.cleaned_data.get('role', 'Employee')
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            AuditLog.log(user=request.user, action='Created', module='User',
                        record_id=str(user.pk), record_repr=f'User {user.username}',
                        ip_address=getattr(request, 'client_ip', None))
            messages.success(request, f'User {user.username} created.')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'welfare_app/users/form.html', {'form': form, 'active_nav': 'users'})


@login_required
def user_update(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    user_obj = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            role = form.cleaned_data.get('role', profile.role)
            profile.role = role
            profile.save()
            messages.success(request, f'User {user_obj.username} updated.')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user_obj, initial={'role': profile.role})
    return render(request, 'welfare_app/users/form.html', {
        'form': form, 'edit_user': user_obj, 'active_nav': 'users',
    })


@login_required
def user_toggle_active(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    user_obj = get_object_or_404(User, pk=pk)
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    status = 'activated' if user_obj.is_active else 'deactivated'
    messages.success(request, f'User {user_obj.username} {status}.')
    return redirect('user_list')

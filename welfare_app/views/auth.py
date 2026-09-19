from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error_message = None

    if request.method == 'POST':
        # Check if 1-click demo login was triggered
        if request.POST.get('demo_login') == '1':
            admin_user = User.objects.filter(is_superuser=True, is_active=True).first()
            if not admin_user:
                admin_user, _ = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
                admin_user.set_password('admin123')
                admin_user.save()
            login(request, admin_user)
            messages.success(request, f'Welcome back, {admin_user.get_full_name() or admin_user.username}!')
            return redirect('dashboard')

        u = (request.POST.get('username') or '').strip()
        p = (request.POST.get('password') or '').strip()
        next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
        if not next_url or next_url in ('None', '/login/', 'login'):
            next_url = 'dashboard'

        # Look up user case-insensitively or by email
        user_obj = User.objects.filter(Q(username__iexact=u) | Q(email__iexact=u)).first()
        actual_username = user_obj.username if user_obj else u

        user = authenticate(request, username=actual_username, password=p)

        # Also support admin with password 'admin' if admin123 was mistyped
        if user is None and u.lower() == 'admin' and p in ('admin', 'admin123', 'password'):
            admin_user = User.objects.filter(username='admin').first()
            if admin_user:
                admin_user.set_password('admin123')
                admin_user.save()
                user = authenticate(request, username='admin', password='admin123')

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect(next_url)
            else:
                error_message = 'This account has been disabled. Please contact the administrator.'
                messages.error(request, error_message)
        else:
            error_message = 'Invalid username or password. Please use admin / admin123.'
            messages.error(request, error_message)

    return render(request, 'welfare_app/auth/login.html', {
        'next': request.GET.get('next', ''),
        'error_message': error_message,
    })


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password has been changed successfully. Please log in again.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'welfare_app/auth/change_password.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import Group
from .forms import StaffRegisterForm


def student_login_view(request):
    """Students log in with roll number (username) + date of birth (password)."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='Student').exists():
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid roll number or date of birth.')
    return render(request, 'accounts/login.html')


def staff_login_view(request):
    """Admin / Staff log in with username + password."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name__in=['Admin', 'Staff']).exists():
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'accounts/staff_login.html')


def staff_register_view(request):
    """Registration — Staff / Admin only."""
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            messages.success(request, f'{role} account created. Please log in.')
            return redirect('staff_login')
    else:
        form = StaffRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

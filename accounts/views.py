from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def student_login_view(request):
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
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and (
            user.is_superuser or user.groups.filter(name__in=['Admin', 'Staff']).exists()
        ):
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'accounts/staff_login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User, Group
from .models import Student, Marks, Course
from .forms import StudentForm, MarksForm, CourseForm


def _sync_student_user(student):
    """Create or update the Django User linked to this student.
    username = roll_number, password = date_of_birth as YYYY-MM-DD."""
    dob_str = student.date_of_birth.strftime('%Y-%m-%d')
    student_group, _ = Group.objects.get_or_create(name='Student')

    if student.user:
        # Update existing user credentials if roll_number or DOB changed
        user = student.user
        user.username = student.roll_number
        user.set_password(dob_str)
        user.save()
    else:
        # Create a new user
        user, created = User.objects.get_or_create(username=student.roll_number)
        user.set_password(dob_str)
        user.save()
        user.groups.add(student_group)
        student.user = user
        student.save(update_fields=['user'])


@login_required
def dashboard(request):
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_staff = request.user.groups.filter(name='Staff').exists()
    is_student = request.user.groups.filter(name='Student').exists()

    # For student users, fetch their own profile
    student_profile = None
    if is_student and not is_admin and not is_staff:
        try:
            student_profile = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            pass

    return render(request, 'dashboard.html', {
        'is_admin': is_admin,
        'is_staff': is_staff,
        'is_student': is_student,
        'student_profile': student_profile,
    })


@login_required
def student_list(request):
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_staff = request.user.groups.filter(name='Staff').exists()
    is_student = request.user.groups.filter(name='Student').exists()

    # Student users see only their own record
    if is_student and not is_admin and not is_staff:
        try:
            own = Student.objects.get(user=request.user)
            students_qs = Student.objects.filter(pk=own.pk)
        except Student.DoesNotExist:
            students_qs = Student.objects.none()
        q = ''
        paginator = Paginator(students_qs, 10)
        students = paginator.get_page(1)
        return render(request, 'student/student_list.html', {
            'students': students,
            'q': q,
            'is_admin': is_admin,
            'is_staff': is_staff,
        })

    q = request.GET.get('q', '')
    if q:
        students_qs = Student.objects.filter(
            models.Q(name__icontains=q) | models.Q(course__name__icontains=q)
        )
    else:
        students_qs = Student.objects.all()
    paginator = Paginator(students_qs, 10)
    page_number = request.GET.get('page', 1)
    students = paginator.get_page(page_number)
    return render(request, 'student/student_list.html', {
        'students': students,
        'q': q,
        'is_admin': is_admin,
        'is_staff': is_staff,
    })


@login_required
def student_create(request):
    if not (request.user.groups.filter(name='Admin').exists() or
            request.user.groups.filter(name='Staff').exists()):
        raise PermissionDenied
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            _sync_student_user(student)
            messages.success(request, 'Student added successfully!')
            return redirect('student_list')
        else:
            print(form.errors)
    else:
        form = StudentForm()
    return render(request, 'student/student_form.html', {'form': form})


@login_required
def student_update(request, pk):
    if not (request.user.groups.filter(name='Admin').exists() or
            request.user.groups.filter(name='Staff').exists()):
        raise PermissionDenied
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            _sync_student_user(student)
            messages.success(request, 'Student updated successfully!')
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'student/student_form.html', {'form': form})


@login_required
def student_delete(request, pk):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('student_list')
    return render(request, 'student/student_delete.html', {'student': student})


@login_required
def marks_create(request, student_pk):
    if not (request.user.groups.filter(name='Admin').exists() or
            request.user.groups.filter(name='Staff').exists()):
        raise PermissionDenied
    student = get_object_or_404(Student, pk=student_pk)
    if request.method == 'POST':
        form = MarksForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marks added successfully!')
            return redirect('marks_detail', pk=student_pk)
    else:
        form = MarksForm(initial={'student': student})
    return render(request, 'student/marks_form.html', {'form': form, 'student': student})


@login_required
def marks_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_staff = request.user.groups.filter(name='Staff').exists()
    is_student = request.user.groups.filter(name='Student').exists()

    # Student users can only view their own marks
    if is_student and not is_admin and not is_staff:
        if student.user != request.user:
            raise PermissionDenied

    marks = Marks.objects.filter(student=student)
    return render(request, 'student/marks_detail.html', {
        'student': student,
        'marks': marks,
        'is_admin': is_admin,
        'is_staff': is_staff,
    })


@login_required
def course_list(request):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    courses = Course.objects.all()
    return render(request, 'student/course_list.html', {'courses': courses})


@login_required
def course_create(request):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course added successfully!')
            return redirect('course_list')
    else:
        form = CourseForm()
    return render(request, 'student/course_form.html', {'form': form})


@login_required
def course_update(request, pk):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'student/course_form.html', {'form': form, 'course': course})


@login_required
def course_delete(request, pk):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('course_list')
    return render(request, 'student/course_delete.html', {'course': course})

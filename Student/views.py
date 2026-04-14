from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User, Group
from .models import Student, Marks, Course
from .forms import StudentForm, MarksForm, CourseForm


def _sync_student_user(student, old_roll=None, old_dob=None):
    """Create or update the Django User linked to this student.
    username = roll_number, password = date_of_birth (YYYY-MM-DD).
    Password is only reset when roll_number or DOB actually changes."""
    dob_str = student.date_of_birth.strftime('%Y-%m-%d')
    student_group, _ = Group.objects.get_or_create(name='Student')

    if student.user:
        user = student.user
        credentials_changed = (
            (old_roll is not None and old_roll != student.roll_number) or
            (old_dob is not None and old_dob != student.date_of_birth)
        )
        user.username = student.roll_number
        if credentials_changed:
            user.set_password(dob_str)
        user.save()
    else:
        user, _ = User.objects.get_or_create(username=student.roll_number)
        user.set_password(dob_str)
        user.save()
        user.groups.add(student_group)
        student.user = user
        student.save(update_fields=['user'])


# ── Dashboard ──────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_staff = request.user.groups.filter(name='Staff').exists()
    is_student = request.user.groups.filter(name='Student').exists()

    student_profile = None
    summary = None

    if is_student and not is_admin and not is_staff:
        try:
            student_profile = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            pass

    if is_admin or is_staff:
        from django.contrib.auth.models import User as AuthUser
        summary = {
            'total_students': Student.objects.count(),
            'total_courses': Course.objects.count(),
            'total_staff': AuthUser.objects.filter(
                groups__name__in=['Admin', 'Staff']
            ).distinct().count(),
        }

    # Top CGPA student per course (visible to all roles)
    top_performers = []
    for course in Course.objects.all():
        students_in_course = Student.objects.filter(course=course).prefetch_related('marks_set')
        best = None
        best_cgpa = -1
        for s in students_in_course:
            c = s.cgpa
            if c is not None and c > best_cgpa:
                best_cgpa = c
                best = s
        if best and best_cgpa > 9.0:
            top_performers.append({
                'course': course.name,
                'student': best.name,
                'cgpa': best_cgpa,
            })

    return render(request, 'dashboard.html', {
        'is_admin': is_admin,
        'is_staff': is_staff,
        'is_student': is_student,
        'student_profile': student_profile,
        'summary': summary,
        'top_performers': top_performers,
    })


# ── Student CRUD ───────────────────────────────────────────────────────────

@login_required
def student_list(request):
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_staff = request.user.groups.filter(name='Staff').exists()
    is_student = request.user.groups.filter(name='Student').exists()

    if is_student and not is_admin and not is_staff:
        try:
            own = Student.objects.get(user=request.user)
            students_qs = Student.objects.filter(pk=own.pk)
        except Student.DoesNotExist:
            students_qs = Student.objects.none()
        students = Paginator(students_qs, 10).get_page(1)
        return render(request, 'student/student_list.html', {
            'students': students, 'q': '',
            'is_admin': is_admin, 'is_staff': is_staff,
        })

    q = request.GET.get('q', '')
    qs = Student.objects.filter(
        models.Q(name__icontains=q) | models.Q(course__name__icontains=q)
    ) if q else Student.objects.all()

    students = Paginator(qs, 10).get_page(request.GET.get('page', 1))
    return render(request, 'student/student_list.html', {
        'students': students, 'q': q,
        'is_admin': is_admin, 'is_staff': is_staff,
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
        messages.error(request, 'Please correct the errors below.')
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
        old_roll, old_dob = student.roll_number, student.date_of_birth
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            _sync_student_user(student, old_roll=old_roll, old_dob=old_dob)
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


# ── Marks ──────────────────────────────────────────────────────────────────

@login_required
def marks_create(request, student_pk):
    if not (request.user.groups.filter(name='Admin').exists() or
            request.user.groups.filter(name='Staff').exists()):
        raise PermissionDenied
    student = get_object_or_404(Student, pk=student_pk)
    if request.method == 'POST':
        form = MarksForm(request.POST, student=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marks added successfully!')
            return redirect('marks_detail', pk=student_pk)
    else:
        form = MarksForm(student=student)
    return render(request, 'student/marks_form.html', {'form': form, 'student': student})


@login_required
def marks_update(request, pk):
    if not (request.user.groups.filter(name='Admin').exists() or
            request.user.groups.filter(name='Staff').exists()):
        raise PermissionDenied
    mark = get_object_or_404(Marks, pk=pk)
    student = mark.student
    if request.method == 'POST':
        form = MarksForm(request.POST, instance=mark, student=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marks updated successfully!')
            return redirect('marks_detail', pk=student.pk)
    else:
        form = MarksForm(instance=mark, student=student)
    return render(request, 'student/marks_form.html', {'form': form, 'student': student, 'editing': True})


@login_required
def marks_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    is_admin = request.user.groups.filter(name='Admin').exists()
    is_staff = request.user.groups.filter(name='Staff').exists()
    is_student = request.user.groups.filter(name='Student').exists()

    if is_student and not is_admin and not is_staff:
        if student.user != request.user:
            raise PermissionDenied

    marks = Marks.objects.filter(student=student)
    return render(request, 'student/marks_detail.html', {
        'student': student, 'marks': marks,
        'is_admin': is_admin, 'is_staff': is_staff,
    })


# ── Courses ────────────────────────────────────────────────────────────────

@login_required
def course_list(request):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    return render(request, 'student/course_list.html', {'courses': Course.objects.all()})


@login_required
def course_create(request):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    form = CourseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Course added successfully!')
        return redirect('course_list')
    return render(request, 'student/course_form.html', {'form': form})


@login_required
def course_update(request, pk):
    if not request.user.groups.filter(name='Admin').exists():
        raise PermissionDenied
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=course)
    if form.is_valid():
        form.save()
        messages.success(request, 'Course updated successfully!')
        return redirect('course_list')
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



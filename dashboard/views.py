from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from students.models import Student
from staff.models import Staff

@login_required
def dashboard_home_view(request):
    if request.user.is_superuser or request.user.role == 'SUPER_ADMIN':
        return redirect('admin_dashboard')
    elif request.user.role == 'STAFF':
        return redirect('staff_dashboard')
    elif request.user.role == 'STUDENT':
        return redirect('student_dashboard')
    else:
        return redirect('login')

@login_required
@role_required('SUPER_ADMIN')
def admin_dashboard_view(request):
    context = {
        'total_students': 1250,
        'total_staff': 85,
        'total_courses': 18,
        'pending_fees': "$15,430",
        'role_title': 'Super Admin'
    }
    return render(request, 'dashboard/admin.html', context)

@login_required
@role_required('STAFF')
def staff_dashboard_view(request):
    staff = get_object_or_404(Staff, user=request.user)
    context = {
        'staff_member': staff,
        'assigned_classes_count': 4,
        'pending_assignments': 3,
        'today_lectures': 3,
        'messages_count': 5,
        'role_title': 'Staff',
        'student_count': 148,
        'assigned_subjects_count': 3,
        'today_classes': [
            {'time': '09:00 AM - 10:30 AM', 'subject': 'Object Oriented Programming', 'room': 'Lab 3', 'class': 'CSE-A Sem 1'},
            {'time': '11:00 AM - 12:30 PM', 'subject': 'Advanced Mathematics', 'room': 'Room 102', 'class': 'CSE-A Sem 1'},
            {'time': '02:00 PM - 03:30 PM', 'subject': 'Digital Logic Design', 'room': 'Room 201', 'class': 'ECE-A Sem 1'},
        ],
        'assigned_subjects': [
            {'name': 'Object Oriented Programming', 'code': 'CS-101', 'class': 'CSE-A Sem 1'},
            {'name': 'Advanced Mathematics', 'code': 'MA-101', 'class': 'CSE-A Sem 1'},
            {'name': 'Digital Logic Design', 'code': 'EC-101', 'class': 'ECE-A Sem 1'},
        ],
        'leave_requests': [
            {'reason': 'Medical Checkup', 'date': 'July 5, 2026', 'status': 'Pending'},
        ],
        'recent_activities': [
            {'activity': 'Marked attendance for OOP Class', 'time': '2 hours ago'},
            {'activity': 'Published Assignment 2 (Math)', 'time': '5 hours ago'},
        ]
    }
    return render(request, 'dashboard/staff.html', context)

@login_required
@role_required('STUDENT')
def student_dashboard_view(request):
    student = get_object_or_404(Student, user=request.user)
    context = {
        'student': student,
        'attendance_percentage': 92.5,
        'upcoming_exams': 2,
        'pending_assignments': 4,
        'gpa': '3.82',
        'role_title': 'Student',
        'timetable_slots': [
            {'time': '09:00 AM - 10:30 AM', 'subject': 'Advanced Mathematics', 'room': 'Room 102'},
            {'time': '11:00 AM - 12:30 PM', 'subject': 'Object Oriented Programming', 'room': 'Lab 3'},
            {'time': '02:00 PM - 03:30 PM', 'subject': 'Digital Logic Design', 'room': 'Room 201'},
        ],
        'assignments': [
            {'title': 'Math Assignment 3', 'due': 'Tomorrow, 11:59 PM', 'class': 'Urgent'},
            {'title': 'OOP Lab Report 2', 'due': 'Friday, 5:00 PM', 'class': 'Normal'},
        ]
    }
    return render(request, 'dashboard/student.html', context)

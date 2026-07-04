import csv
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Count, Q

from accounts.decorators import RoleRequiredMixin
from notifications.models import Notification
from students.models import Student
from staff.models import Staff
from academics.models import Department, Semester, Section, Subject
from .models import StudentAttendance, StaffAttendance, LeaveRequest
from .forms import LeaveRequestForm, LeaveReviewForm, AttendanceImportForm

# ----------------- ATTENDANCE DASHBOARD -----------------
class AttendanceDashboardView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def get(self, request):
        today = datetime.date.today()
        
        # Calculate Student Stats for Today
        total_students = Student.objects.filter(status='ACTIVE').count()
        today_attendance = StudentAttendance.objects.filter(date=today)
        
        present_count = today_attendance.filter(status='PRESENT').count()
        absent_count = today_attendance.filter(status='ABSENT').count()
        late_count = today_attendance.filter(status='LATE').count()
        leave_count = today_attendance.filter(status='LEAVE').count()
        halfday_count = today_attendance.filter(status='HALFDAY').count()
        
        marked_count = today_attendance.count()
        attendance_percentage = 0
        if marked_count > 0:
            # Present + Late + Halfday count as present in terms of ratio
            attending = present_count + late_count + halfday_count
            attendance_percentage = round((attending / marked_count) * 100, 1)

        # Recent Absentee Students
        recent_absentees = today_attendance.filter(status='ABSENT').select_related('student', 'subject')[:10]

        # Faculty Attendance Stats for Today
        total_faculty = Staff.objects.filter(employment_status='ACTIVE').count()
        today_staff_att = StaffAttendance.objects.filter(date=today)
        staff_present = today_staff_att.filter(status='PRESENT').count()
        staff_absent = today_staff_att.filter(status='ABSENT').count()

        # Vanilla SVG Trends / Charts placeholders helper
        context = {
            'today': today,
            'total_students': total_students,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'leave_count': leave_count,
            'halfday_count': halfday_count,
            'attendance_percentage': attendance_percentage,
            'recent_absentees': recent_absentees,
            'total_faculty': total_faculty,
            'staff_present': staff_present,
            'staff_absent': staff_absent,
            'import_form': AttendanceImportForm(),
        }
        return render(request, 'attendance/attendance_dashboard.html', context)


# ----------------- MARK BULK STUDENT ATTENDANCE -----------------
class StudentAttendanceMarkView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def get(self, request):
        departments = Department.objects.all()
        semesters = Semester.objects.all()
        sections = Section.objects.all()
        subjects = Subject.objects.all()
        
        # Load filtered students if parameters specified
        dept_id = request.GET.get('department')
        sem_id = request.GET.get('semester')
        sec_id = request.GET.get('section')
        sub_id = request.GET.get('subject')
        date_str = request.GET.get('date', datetime.date.today().strftime('%Y-%m-%d'))
        
        students_list = []
        existing_attendance = {}
        
        if dept_id and sem_id and sec_id:
            students_list = list(Student.objects.filter(
                department_id=dept_id,
                semester_id=sem_id,
                section_id=sec_id,
                status='ACTIVE'
            ).order_by('register_number'))
            
            # Fetch existing logs for this date/subject
            date_val = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            existing_records = StudentAttendance.objects.filter(
                date=date_val,
                subject_id=sub_id if sub_id else None,
                student__in=students_list
            )
            existing_attendance = {r.student_id: r.status for r in existing_records}
            for student in students_list:
                student.marked_status = existing_attendance.get(student.id, 'PRESENT')

        context = {
            'departments': departments,
            'semesters': semesters,
            'sections': sections,
            'subjects': subjects,
            'students_list': students_list,
            'query': request.GET,
            'today_date': date_str,
        }
        return render(request, 'attendance/mark_attendance.html', context)

    def post(self, request):
        dept_id = request.POST.get('department')
        sem_id = request.POST.get('semester')
        sec_id = request.POST.get('section')
        sub_id = request.POST.get('subject')
        date_str = request.POST.get('date')
        
        if not (dept_id and sem_id and sec_id and date_str):
            messages.error(request, "Missing filter criteria parameters.")
            return redirect('mark_attendance')
            
        date_val = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        subject_obj = Subject.objects.filter(id=sub_id).first() if sub_id else None
        
        students = Student.objects.filter(
            department_id=dept_id,
            semester_id=sem_id,
            section_id=sec_id,
            status='ACTIVE'
        )

        try:
            with transaction.atomic():
                for student in students:
                    status_val = request.POST.get(f'status_{student.id}', 'PRESENT')
                    remarks_val = request.POST.get(f'remarks_{student.id}', '')
                    
                    # Update or create record
                    attendance_rec, created = StudentAttendance.objects.update_or_create(
                        student=student,
                        date=date_val,
                        subject=subject_obj,
                        defaults={
                            'status': status_val,
                            'remarks': remarks_val
                        }
                    )
                    
                    # Trigger notification if absent
                    if status_val == 'ABSENT':
                        Notification.send_notification(
                            user=student.user,
                            title="Absence Alert",
                            message=f"You were marked ABSENT on {date_val} for class slot."
                        )
                
                messages.success(request, f"Attendance records successfully marked for {date_str}.")
        except Exception as e:
            messages.error(request, f"Failed to record attendance: {str(e)}")
            
        return redirect(f"{request.path}?department={dept_id}&semester={sem_id}&section={sec_id}&subject={sub_id or ''}&date={date_str}")


# ----------------- BULK IMPORT ATTENDANCE CSV -----------------
class StudentAttendanceImportView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def post(self, request):
        form = AttendanceImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            
            success_count = 0
            error_count = 0
            
            # Expect header: register_number, date, status, subject_code (optional), remarks (optional)
            next(reader, None)  # skip header
            
            try:
                with transaction.atomic():
                    for row in reader:
                        if not row or len(row) < 3:
                            continue
                        reg_num = row[0].strip()
                        date_str = row[1].strip()
                        status_val = row[2].strip().upper()
                        sub_code = row[3].strip() if len(row) > 3 else ''
                        remarks_val = row[4].strip() if len(row) > 4 else ''
                        
                        student = Student.objects.filter(register_number=reg_num).first()
                        if not student:
                            error_count += 1
                            continue
                            
                        try:
                            date_val = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            error_count += 1
                            continue
                            
                        subject = None
                        if sub_code:
                            subject = Subject.objects.filter(code=sub_code).first()
                            
                        StudentAttendance.objects.update_or_create(
                            student=student,
                            date=date_val,
                            subject=subject,
                            defaults={
                                'status': status_val,
                                'remarks': remarks_val
                            }
                        )
                        success_count += 1
                messages.success(request, f"CSV Import complete: {success_count} records saved, {error_count} records failed.")
            except Exception as e:
                messages.error(request, f"CSV parsing crashed: {str(e)}")
        else:
            messages.error(request, "Invalid CSV upload details.")
            
        return redirect('attendance_dashboard')


# ----------------- EXPORT ATTENDANCE CSV -----------------
class StudentAttendanceExportView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def get(self, request):
        # Generate CSV Stream response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Register Number', 'Student Name', 'Date', 'Subject Code', 'Status', 'Remarks'])
        
        records = StudentAttendance.objects.select_related('student', 'subject').all()[:200]
        for r in records:
            writer.writerow([
                r.student.register_number,
                r.student.full_name,
                r.date,
                r.subject.code if r.subject else 'Daily',
                r.status,
                r.remarks or ''
            ])
            
        return response


# ----------------- LEAVE REQUESTS SELF SERVICE -----------------
class LeaveRequestListView(LoginRequiredMixin, ListView):
    model = LeaveRequest
    template_name = 'attendance/leave_list.html'
    context_object_name = 'leaves'

    def get_queryset(self):
        # Non-admins only see their own requests
        if self.request.user.role == 'SUPER_ADMIN':
            return LeaveRequest.objects.select_related('user').all()
        return LeaveRequest.objects.filter(user=self.request.user)


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'attendance/leave_form.html'
    success_url = reverse_lazy('leave_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'PENDING'
        response = super().form_valid(form)
        
        # Notify admins of new pending leave request
        admins = get_user_model().objects.filter(role='SUPER_ADMIN')
        for admin in admins:
            Notification.send_notification(
                user=admin,
                title="New Leave Request",
                message=f"{self.request.user.username} applied for {form.instance.get_leave_type_display()}."
            )
            
        messages.success(self.request, "Leave request submitted successfully for approval.")
        return response


class LeaveRequestCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk, user=request.user)
        if leave.status == 'PENDING':
            leave.delete()
            messages.success(request, "Leave request cancelled and removed.")
        else:
            messages.error(request, "Only pending leave requests can be cancelled.")
        return redirect('leave_list')


# ----------------- LEAVE REQUEST REVIEWS QUEUE -----------------
class LeaveReviewListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = LeaveRequest
    template_name = 'attendance/leave_review_list.html'
    context_object_name = 'leaves'
    roles = ['SUPER_ADMIN', 'STAFF']
    
    def get_queryset(self):
        # Review list only displays pending leaves
        return LeaveRequest.objects.filter(status='PENDING').select_related('user')


class LeaveReviewView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        status_val = request.POST.get('status')
        comments = request.POST.get('admin_comments', '')
        
        if status_val in ['APPROVED', 'REJECTED']:
            leave.status = status_val
            leave.reviewed_by = request.user
            leave.admin_comments = comments
            leave.save()
            
            # Send Notification back to target applicant
            Notification.send_notification(
                user=leave.user,
                title=f"Leave Request {status_val.capitalize()}",
                message=f"Your leave request from {leave.start_date} to {leave.end_date} was {status_val.lower()}."
            )
            
            # If approved and student, automatically write 'LEAVE' record into attendance logs
            if status_val == 'APPROVED' and hasattr(leave.user, 'student_profile'):
                student = leave.user.student_profile
                curr = leave.start_date
                while curr <= leave.end_date:
                    StudentAttendance.objects.update_or_create(
                        student=student,
                        date=curr,
                        subject=None,
                        defaults={'status': 'LEAVE', 'remarks': f"Approved Leave: {leave.reason}"}
                    )
                    curr += datetime.timedelta(days=1)
            
            messages.success(request, f"Leave request is now resolved: {status_val}.")
        else:
            messages.error(request, "Invalid leave status selection.")
            
        return redirect('leave_review_list')


# Import User helper
from django.contrib.auth import get_user_model

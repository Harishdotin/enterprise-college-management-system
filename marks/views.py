import csv
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Count, Q, Avg, Sum, F, DecimalField
from django.contrib.auth import get_user_model

from accounts.decorators import RoleRequiredMixin
from notifications.models import Notification
from students.models import Student
from staff.models import Staff
from academics.models import Department, Semester, Section, Course, Subject, AcademicYear
from .models import GradeRule, Exam, StudentMark
from .forms import ExamForm, GradeRuleForm, MarksEntryForm, MarksBulkUploadForm

User = get_user_model()

# ----------------- EXAMINATIONS CRUD -----------------
class ExamListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Exam
    template_name = 'marks/exam_list.html'
    context_object_name = 'exams'
    roles = ['SUPER_ADMIN', 'STAFF']
    paginate_by = 10

    def get_queryset(self):
        qs = Exam.objects.select_related('department', 'semester__course', 'subject').all()
        
        # Filters
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(subject__code__icontains=search))
            
        dept = self.request.GET.get('department', '')
        if dept:
            qs = qs.filter(department_id=dept)
            
        sem = self.request.GET.get('semester', '')
        if sem:
            qs = qs.filter(semester_id=sem)
            
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
            
        return qs.order_by('-exam_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        context['semesters'] = Semester.objects.all()
        context['query_params'] = self.request.GET.dict()
        return context


class ExamCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('exam_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        response = super().form_valid(form)
        exam = self.object
        
        # If published, automatically notify students in the course/semester
        if exam.status == 'PUBLISHED':
            students = Student.objects.filter(course=exam.course, semester=exam.semester, status='ACTIVE')
            for student in students:
                Notification.send_notification(
                    user=student.user,
                    title="New Exam Scheduled",
                    message=f"Exam '{exam.name}' for {exam.subject.name} has been scheduled on {exam.exam_date}."
                )
        messages.success(self.request, "Exam scheduled successfully.")
        return response


class ExamUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('exam_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Exam parameters modified.")
        return super().form_valid(form)


class ExamDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Exam
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('exam_list')
    roles = ['SUPER_ADMIN']


class ExamPublishView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN']

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        if exam.status == 'DRAFT':
            exam.status = 'PUBLISHED'
            exam.save()
            
            # Notify students
            students = Student.objects.filter(course=exam.course, semester=exam.semester, status='ACTIVE')
            for student in students:
                Notification.send_notification(
                    user=student.user,
                    title="Exam Schedule Published",
                    message=f"Schedule details for '{exam.name}' are now active. Exam date is {exam.exam_date}."
                )
            messages.success(request, "Exam published to portal.")
        return redirect('exam_list')


# ----------------- MARKS ENTRY PORTAL -----------------
class MarksEntryView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # Load students registered in this Course/Semester/Section
        students = Student.objects.filter(
            course=exam.course,
            semester=exam.semester,
            status='ACTIVE'
        ).order_by('register_number')
        if exam.section:
            students = students.filter(section=exam.section)

        # Retrieve existing marks
        existing_marks = StudentMark.objects.filter(exam=exam)
        marks_dict = {m.student_id: m.marks_obtained for m in existing_marks}
        remarks_dict = {m.student_id: m.remarks for m in existing_marks}

        # Inject existing values to students list
        students_list = list(students)
        for s in students_list:
            s.marks_entered = marks_dict.get(s.id, '')
            s.remarks_entered = remarks_dict.get(s.id, '')

        context = {
            'exam': exam,
            'students_list': students_list,
            'bulk_form': MarksBulkUploadForm(),
        }
        return render(request, 'marks/marks_entry.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        students = Student.objects.filter(
            course=exam.course,
            semester=exam.semester,
            status='ACTIVE'
        )
        if exam.section:
            students = students.filter(section=exam.section)

        try:
            with transaction.atomic():
                for student in students:
                    marks_str = request.POST.get(f'marks_{student.id}', '').strip()
                    remarks_val = request.POST.get(f'remarks_{student.id}', '')
                    
                    if marks_str != '':
                        val = float(marks_str)
                        # Save student marks
                        StudentMark.objects.update_or_create(
                            exam=exam,
                            student=student,
                            defaults={
                                'marks_obtained': val,
                                'remarks': remarks_val
                            }
                        )
                    else:
                        # Clear existing log if sent empty
                        StudentMark.objects.filter(exam=exam, student=student).delete()
                        
                messages.success(request, f"Marks roster for '{exam.name}' has been updated.")
        except Exception as e:
            messages.error(request, f"Failure writing marks: {str(e)}")
            
        return redirect('marks_entry', exam_id=exam.id)


class MarksBulkUploadView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        form = MarksBulkUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            
            success_count = 0
            error_count = 0
            
            # Header: register_number, marks_obtained, remarks (optional)
            next(reader, None)
            
            try:
                with transaction.atomic():
                    for row in reader:
                        if not row or len(row) < 2:
                            continue
                        reg = row[0].strip()
                        marks_str = row[1].strip()
                        remarks = row[2].strip() if len(row) > 2 else ''
                        
                        student = Student.objects.filter(register_number=reg).first()
                        if not student:
                            error_count += 1
                            continue
                            
                        try:
                            val = float(marks_str)
                            if val > exam.maximum_marks or val < 0:
                                error_count += 1
                                continue
                        except ValueError:
                            error_count += 1
                            continue
                            
                        StudentMark.objects.update_or_create(
                            exam=exam,
                            student=student,
                            defaults={
                                'marks_obtained': val,
                                'remarks': remarks
                            }
                        )
                        success_count += 1
                messages.success(request, f"Marks CSV Import complete: {success_count} rows imported, {error_count} failed.")
            except Exception as e:
                messages.error(request, f"Crashed during upload parsing: {str(e)}")
        else:
            messages.error(request, "Invalid CSV file uploads.")
            
        return redirect('marks_entry', exam_id=exam.id)


class MarksExportView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="marks_export_{exam.id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Register Number', 'Student Name', 'Marks Obtained', 'Remarks'])
        
        marks = StudentMark.objects.filter(exam=exam).select_related('student')
        for m in marks:
            writer.writerow([
                m.student.register_number,
                m.student.full_name,
                m.marks_obtained,
                m.remarks or ''
            ])
        return response


# ----------------- RESULT PUBLISHING & GPA / CGPA -----------------
class PublishResultsView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN']

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        exam.status = 'RESULTS_PUBLISHED'
        exam.save()
        
        # Notify student group
        students = Student.objects.filter(course=exam.course, semester=exam.semester, status='ACTIVE')
        for student in students:
            Notification.send_notification(
                user=student.user,
                title="Marks & Results Published",
                message=f"Results for '{exam.name}' ({exam.subject.name}) are now active. Check your results tab."
            )
            
        messages.success(request, f"Exam results published to student portals.")
        return redirect('exam_list')


class StudentResultsView(LoginRequiredMixin, View):
    def get(self, request):
        # Student views their personal gradesheet
        student = getattr(request.user, 'student_profile', None)
        
        # If admin/staff looking up student result via query
        lookup_reg = request.GET.get('register_number')
        if lookup_reg and request.user.role in ['SUPER_ADMIN', 'STAFF']:
            student = Student.objects.filter(register_number=lookup_reg).first()
            
        if not student:
            messages.error(request, "Student profile record not found.")
            return redirect('dashboard_home')

        # Retrieve published marks
        marks = StudentMark.objects.filter(
            student=student,
            exam__status='RESULTS_PUBLISHED'
        ).select_related('exam__subject', 'exam__semester')

        # Group marks by Semester for GPA calculations
        semesters_data = {}
        total_gp_sum = 0
        total_credits = 0

        # Build structures
        for m in marks:
            sem = m.exam.semester
            if sem not in semesters_data:
                semesters_data[sem] = {
                    'marks': [],
                    'gp_sum': 0,
                    'credits_sum': 0,
                    'gpa': 0
                }
            
            credits = m.exam.subject.credits
            gp = m.grade_point
            
            semesters_data[sem]['marks'].append(m)
            semesters_data[sem]['gp_sum'] += (gp * credits)
            semesters_data[sem]['credits_sum'] += credits

        # Calculate GPA per semester
        for sem, data in semesters_data.items():
            if data['credits_sum'] > 0:
                data['gpa'] = round(data['gp_sum'] / data['credits_sum'], 2)
                total_gp_sum += data['gp_sum']
                total_credits += data['credits_sum']

        # Overall CGPA
        cgpa = 0
        if total_credits > 0:
            cgpa = round(total_gp_sum / total_credits, 2)

        # Credits Earned (passing grade rules is_pass, default letters != RA)
        earned_credits = 0
        for m in marks:
            if m.grade_letter != 'RA':
                earned_credits += m.exam.subject.credits

        context = {
            'student_profile': student,
            'semesters_data': semesters_data,
            'overall_cgpa': cgpa,
            'total_credits_earned': earned_credits,
            'total_credits_remaining': max(0, 160 - earned_credits),  # assume 160 degree requirement
        }
        return render(request, 'marks/results_view.html', context)


# ----------------- HALL TICKET GENERATION -----------------
class StudentHallTicketView(LoginRequiredMixin, View):
    def get(self, request):
        student = getattr(request.user, 'student_profile', None)
        
        # lookup for admin/staff
        lookup_reg = request.GET.get('register_number')
        if lookup_reg and request.user.role in ['SUPER_ADMIN', 'STAFF']:
            student = Student.objects.filter(register_number=lookup_reg).first()
            
        if not student:
            messages.error(request, "Student credentials profile not bound.")
            return redirect('dashboard_home')

        # Fetch active exams scheduled for student course & semester
        exams = Exam.objects.filter(
            course=student.course,
            semester=student.semester,
            status='PUBLISHED'
        ).select_related('subject')

        # Trigger notification only when student first prints it
        if request.user.role == 'STUDENT':
            Notification.send_notification(
                user=request.user,
                title="Hall Ticket Accessed",
                message=f"Your official hall ticket was generated on {datetime.date.today()}."
            )

        context = {
            'student': student,
            'exams': exams,
            'today_date': datetime.date.today(),
            'seat_number': f"S-{student.id}-{100 + student.id}",
        }
        return render(request, 'marks/hall_ticket.html', context)


# ----------------- ACADEMIC PERFORMANCE ANALYTICS -----------------
class AcademicPerformanceView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def get(self, request):
        # Aggregate stats
        total_exams = Exam.objects.filter(status='RESULTS_PUBLISHED').count()
        marks = StudentMark.objects.filter(exam__status='RESULTS_PUBLISHED')
        
        total_marks_count = marks.count()
        pass_marks = marks.filter(~Q(grade_letter='RA')).count()
        
        pass_pct = 0
        fail_pct = 0
        if total_marks_count > 0:
            pass_pct = round((pass_marks / total_marks_count) * 100, 1)
            fail_pct = round(100 - pass_pct, 1)

        # GPA distribution details
        grade_distribution = marks.values('grade_letter').annotate(count=Count('id')).order_by('-count')

        # Top performers list (Avg GPA score)
        top_performers = StudentMark.objects.filter(
            exam__status='RESULTS_PUBLISHED'
        ).values(
            'student__register_number', 'student__full_name'
        ).annotate(
            avg_gp=Avg('grade_point')
        ).order_by('-avg_gp')[:10]

        context = {
            'total_exams': total_exams,
            'pass_pct': pass_pct,
            'fail_pct': fail_pct,
            'grade_distribution': grade_distribution,
            'top_performers': top_performers,
        }
        return render(request, 'marks/analytics_dashboard.html', context)

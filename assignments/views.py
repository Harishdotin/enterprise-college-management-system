from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone

from accounts.decorators import RoleRequiredMixin
from notifications.models import Notification
from students.models import Student
from academics.models import Department, Semester, Course, Subject
from .models import Assignment, AssignmentSubmission, StudyMaterial
from .forms import AssignmentForm, AssignmentSubmissionForm, AssignmentGradeForm, StudyMaterialForm

# ----------------- ASSIGNMENTS -----------------
class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 10

    def get_queryset(self):
        qs = Assignment.objects.select_related('department', 'course', 'semester', 'subject', 'created_by').all()
        
        # If student, filter by student's department/course/semester
        if self.request.user.role == 'STUDENT':
            student = getattr(self.request.user, 'student_profile', None)
            if student:
                qs = qs.filter(course=student.course, semester=student.semester)
                
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(subject__code__icontains=search))
            
        subject_id = self.request.GET.get('subject', '')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
            
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all()
        context['query_params'] = self.request.GET.dict()
        
        # If student, attach submission status to each assignment
        if self.request.user.role == 'STUDENT':
            student = getattr(self.request.user, 'student_profile', None)
            if student:
                submissions = AssignmentSubmission.objects.filter(student=student)
                sub_dict = {s.assignment_id: s for s in submissions}
                for a in context['assignments']:
                    a.student_submission = sub_dict.get(a.id)
        return context


class AssignmentCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('assignment_list')
    roles = ['SUPER_ADMIN', 'STAFF']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        assignment = self.object
        
        # Notify students matching course/semester
        students = Student.objects.filter(course=assignment.course, semester=assignment.semester, status='ACTIVE')
        for student in students:
            Notification.send_notification(
                user=student.user,
                title="New Assignment Posted",
                message=f"Assignment '{assignment.title}' for {assignment.subject.name} has been posted. Due: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}."
            )
        messages.success(self.request, "Assignment posted successfully.")
        return response


class AssignmentUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('assignment_list')
    roles = ['SUPER_ADMIN', 'STAFF']


class AssignmentDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Assignment
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('assignment_list')
    roles = ['SUPER_ADMIN', 'STAFF']


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.object
        if self.request.user.role == 'STUDENT':
            student = getattr(self.request.user, 'student_profile', None)
            context['submission'] = AssignmentSubmission.objects.filter(assignment=assignment, student=student).first()
            context['submission_form'] = AssignmentSubmissionForm()
        else:
            context['submissions'] = AssignmentSubmission.objects.filter(assignment=assignment).select_related('student')
        return context


class AssignmentSubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        student = getattr(request.user, 'student_profile', None)
        if not student:
            messages.error(request, "Only students can submit assignments.")
            return redirect('assignment_detail', pk=pk)

        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission, created = AssignmentSubmission.objects.update_or_create(
                assignment=assignment,
                student=student,
                defaults={'file': form.cleaned_data['file']}
            )
            if submission.is_late:
                messages.warning(request, "Assignment submitted, but recorded as LATE since the due date passed.")
            else:
                messages.success(request, "Assignment submitted successfully!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
        return redirect('assignment_detail', pk=pk)


class AssignmentGradeView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def post(self, request, pk):
        submission = get_object_or_404(AssignmentSubmission, pk=pk)
        form = AssignmentGradeForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            Notification.send_notification(
                user=submission.student.user,
                title="Assignment Graded",
                message=f"Your submission for '{submission.assignment.title}' has been graded: {submission.marks_obtained}/{submission.assignment.maximum_marks}."
            )
            messages.success(request, "Grade recorded successfully.")
        else:
            messages.error(request, "Invalid grading parameters.")
        return redirect('assignment_detail', pk=submission.assignment.id)


# ----------------- STUDY MATERIALS -----------------
class StudyMaterialListView(LoginRequiredMixin, ListView):
    model = StudyMaterial
    template_name = 'assignments/study_materials.html'
    context_object_name = 'materials'
    paginate_by = 12

    def get_queryset(self):
        qs = StudyMaterial.objects.select_related('department', 'course', 'semester', 'subject', 'uploaded_by').all()
        
        if self.request.user.role == 'STUDENT':
            student = getattr(self.request.user, 'student_profile', None)
            if student:
                qs = qs.filter(course=student.course, semester=student.semester)
                
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(subject__code__icontains=search) | Q(subject__name__icontains=search))
            
        subject_id = self.request.GET.get('subject', '')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
            
        return qs.order_by('-uploaded_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all()
        context['form'] = StudyMaterialForm()
        context['query_params'] = self.request.GET.dict()
        return context


class StudyMaterialUploadView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN', 'STAFF']

    def post(self, request):
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.uploaded_by = request.user
            material.save()
            messages.success(request, f"Study material '{material.title}' uploaded successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
        return redirect('study_material_list')

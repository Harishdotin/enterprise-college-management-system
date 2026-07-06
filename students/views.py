from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.contrib.auth import get_user_model

from accounts.decorators import RoleRequiredMixin
from .models import Student
from .forms import StudentForm, StudentProfileForm
from academics.models import Department, Course, Semester

User = get_user_model()

class StudentListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 10
    roles = ['SUPER_ADMIN', 'STAFF']

    def get_queryset(self):
        queryset = Student.objects.select_related('department', 'course', 'semester', 'user').all()
        
        # Search filter
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(register_number__icontains=search_query) |
                Q(admission_number__icontains=search_query) |
                Q(email__icontains=search_query)
            )
            
        # Dropdown filters
        dept_filter = self.request.GET.get('department', '')
        if dept_filter:
            queryset = queryset.filter(department_id=dept_filter)
            
        course_filter = self.request.GET.get('course', '')
        if course_filter:
            queryset = queryset.filter(course_id=course_filter)
            
        sem_filter = self.request.GET.get('semester', '')
        if sem_filter:
            queryset = queryset.filter(semester_id=sem_filter)
            
        sec_filter = self.request.GET.get('section', '')
        if sec_filter:
            queryset = queryset.filter(section__iexact=sec_filter)
            
        ay_filter = self.request.GET.get('academic_year', '')
        if ay_filter:
            queryset = queryset.filter(academic_year=ay_filter)
            
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Sorting
        sort_by = self.request.GET.get('sort', 'register_number')
        if sort_by in ['register_number', '-register_number', 'full_name', '-full_name', 'created_date', '-created_date']:
            queryset = queryset.order_by(sort_by)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all().order_by('name')
        context['courses'] = Course.objects.all().order_by('name')
        context['semesters'] = Semester.objects.all().order_by('course__code', 'number')
        context['query_params'] = self.request.GET.dict()
        return context


class StudentCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')
    roles = ['SUPER_ADMIN', 'STAFF']

    def get(self, request, *args, **kwargs):
        print("Departments in DB:", Department.objects.count())
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                reg_num = form.cleaned_data['register_number']
                email = form.cleaned_data['email']
                full_name = form.cleaned_data['full_name']
                phone = form.cleaned_data['phone_number']
                
                names = full_name.split(' ', 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ''
                
                # Create User Account
                user = User.objects.create_user(
                    username=reg_num,
                    email=email,
                    password="Password@123",  # default credential
                    role='STUDENT',
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone
                )
                
                # Create Student Profile
                student = form.save(commit=False)
                student.user = user
                student.created_by = self.request.user
                student.save()

                self.object = student
                
                messages.success(self.request, f"Student {student.full_name} registered successfully. Default login password is 'Password@123'.")
                return redirect(self.get_success_url())
        except Exception as e:
            raise


class StudentUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')
    roles = ['SUPER_ADMIN', 'STAFF']

    def form_valid(self, form):
        try:
            with transaction.atomic():
                student = form.save()
                user = student.user
                user.email = student.email
                names = student.full_name.split(' ', 1)
                user.first_name = names[0]
                user.last_name = names[1] if len(names) > 1 else ''
                user.phone_number = student.phone_number
                user.save()
                
                messages.success(self.request, f"Student {student.full_name} updated successfully.")
                return redirect(self.get_success_url())
        except Exception as e:
            form.add_error(None, f"Error updating user account: {str(e)}")
            return self.form_invalid(form)


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def dispatch(self, request, *args, **kwargs):
        student = self.get_object()
        if request.user.role in ['SUPER_ADMIN', 'STAFF'] or request.user == student.user:
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "Access denied. You do not have permission to view this profile.")
        return redirect('access_denied')


class StudentDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')
    roles = ['SUPER_ADMIN']

    def post(self, request, *args, **kwargs):
        student = self.get_object()
        try:
            with transaction.atomic():
                student.user.delete()  # Cascades and deletes the student profile
                messages.success(request, f"Student {student.full_name} deleted successfully.")
                return redirect(self.get_success_url())
        except Exception as e:
            messages.error(request, f"Error deleting student: {str(e)}")
            return redirect('student_list')


class StudentSelfProfileView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentProfileForm
    template_name = 'students/profile.html'
    
    def get_object(self, queryset=None):
        return get_object_or_404(Student, user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if request.user.role == 'STUDENT':
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "Access restricted to student accounts.")
        return redirect('access_denied')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                student = form.save()
                user = student.user
                user.email = student.email
                names = student.full_name.split(' ', 1)
                user.first_name = names[0]
                user.last_name = names[1] if len(names) > 1 else ''
                user.phone_number = student.phone_number
                user.save()
                messages.success(self.request, "Your profile details have been updated successfully.")
                return redirect('student_self_profile')
        except Exception as e:
            form.add_error(None, f"Error updating profile: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('student_self_profile')


from .models import Feedback
from .forms import FeedbackForm
from django.db.models import Avg, Count

class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'students/feedback_form.html'
    success_url = reverse_lazy('student_feedback_create')

    def form_valid(self, form):
        feedback = form.save(commit=False)
        if self.request.user.role == 'STUDENT':
            student = getattr(self.request.user, 'student_profile', None)
            if student and not feedback.is_anonymous:
                feedback.student = student
        if feedback.is_anonymous:
            feedback.student = None
        feedback.save()
        messages.success(self.request, "Thank you! Your feedback has been submitted successfully.")
        return super().form_valid(form)


class FeedbackAnalyticsView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Feedback
    template_name = 'students/feedback_analytics.html'
    context_object_name = 'feedbacks'
    roles = ['SUPER_ADMIN']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['avg_rating'] = Feedback.objects.aggregate(avg=Avg('rating'))['avg'] or 0
        context['type_counts'] = Feedback.objects.values('feedback_type').annotate(count=Count('id'))
        return context


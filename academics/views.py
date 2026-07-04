from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q

from accounts.decorators import RoleRequiredMixin
from .models import Department, Course, Semester, Section, Subject, Class, FacultySubjectAssignment, AcademicYear
from .forms import (
    DepartmentForm, CourseForm, SemesterForm, SectionForm, 
    SubjectForm, ClassForm, FacultySubjectAssignmentForm, AcademicYearForm
)

# ----------------- ACADEMIC YEAR -----------------
class AcademicYearListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = AcademicYear
    template_name = 'academics/year_list.html'
    context_object_name = 'years'
    roles = ['SUPER_ADMIN']
    ordering = ['-academic_year']


class AcademicYearCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('year_list')
    roles = ['SUPER_ADMIN']
    
    def form_valid(self, form):
        messages.success(self.request, "Academic Year created successfully.")
        return super().form_valid(form)


class AcademicYearUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('year_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Academic Year updated successfully.")
        return super().form_valid(form)


class AcademicYearDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = AcademicYear
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('year_list')
    roles = ['SUPER_ADMIN']

    def post(self, request, *args, **kwargs):
        messages.success(self.request, "Academic Year deleted successfully.")
        return super().post(request, *args, **kwargs)


# ----------------- DEPARTMENT -----------------
class DepartmentListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Department
    template_name = 'academics/department_list.html'
    context_object_name = 'departments'
    roles = ['SUPER_ADMIN']
    paginate_by = 10

    def get_queryset(self):
        qs = Department.objects.select_related('hod').all()
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('code')


class DepartmentCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('department_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Department created successfully.")
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('department_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Department updated successfully.")
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Department
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('department_list')
    roles = ['SUPER_ADMIN']


# ----------------- COURSE -----------------
class CourseListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Course
    template_name = 'academics/course_list.html'
    context_object_name = 'courses'
    roles = ['SUPER_ADMIN']
    paginate_by = 10

    def get_queryset(self):
        qs = Course.objects.select_related('department').all()
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
        dept = self.request.GET.get('department', '')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs.order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context


class CourseCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('course_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Course program registered successfully.")
        return super().form_valid(form)


class CourseUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('course_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Course updated successfully.")
        return super().form_valid(form)


class CourseDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Course
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('course_list')
    roles = ['SUPER_ADMIN']


# ----------------- SEMESTER -----------------
class SemesterListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Semester
    template_name = 'academics/semester_list.html'
    context_object_name = 'semesters'
    roles = ['SUPER_ADMIN']
    paginate_by = 10

    def get_queryset(self):
        qs = Semester.objects.select_related('course', 'academic_year').all()
        course = self.request.GET.get('course', '')
        if course:
            qs = qs.filter(course_id=course)
        return qs.order_by('course__code', 'number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all()
        return context


class SemesterCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('semester_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Academic Semester registered successfully.")
        return super().form_valid(form)


class SemesterUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('semester_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Semester term details updated successfully.")
        return super().form_valid(form)


class SemesterDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Semester
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('semester_list')
    roles = ['SUPER_ADMIN']


# ----------------- SECTION -----------------
class SectionListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Section
    template_name = 'academics/section_list.html'
    context_object_name = 'sections'
    roles = ['SUPER_ADMIN']
    paginate_by = 10

    def get_queryset(self):
        qs = Section.objects.select_related('department', 'semester__course', 'class_advisor').all()
        dept = self.request.GET.get('department', '')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs.order_by('semester__course__code', 'semester__number', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context


class SectionCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('section_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Class Section created successfully.")
        return super().form_valid(form)


class SectionUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('section_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Section advisor and details updated.")
        return super().form_valid(form)


class SectionDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Section
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('section_list')
    roles = ['SUPER_ADMIN']


# ----------------- SUBJECT -----------------
class SubjectListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Subject
    template_name = 'academics/subject_list.html'
    context_object_name = 'subjects'
    roles = ['SUPER_ADMIN']
    paginate_by = 10

    def get_queryset(self):
        qs = Subject.objects.select_related('department', 'semester__course', 'faculty').all()
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
        dept = self.request.GET.get('department', '')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs.order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context


class SubjectCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('subject_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Academic Subject registered successfully.")
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('subject_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Subject configuration updated.")
        return super().form_valid(form)


class SubjectDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Subject
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('subject_list')
    roles = ['SUPER_ADMIN']


# ----------------- CLASS -----------------
class ClassListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Class
    template_name = 'academics/class_list.html'
    context_object_name = 'classes'
    roles = ['SUPER_ADMIN']
    paginate_by = 10

    def get_queryset(self):
        qs = Class.objects.select_related('department', 'course', 'semester', 'section', 'class_advisor').all()
        dept = self.request.GET.get('department', '')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs.order_by('course__code', 'semester__number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context


class ClassCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('class_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Active class record established.")
        return super().form_valid(form)


class ClassUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('class_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Class record parameters updated.")
        return super().form_valid(form)


class ClassDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Class
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('class_list')
    roles = ['SUPER_ADMIN']


# ----------------- FACULTY ASSIGNMENT -----------------
class FacultyAssignmentListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = FacultySubjectAssignment
    template_name = 'academics/assignment_list.html'
    context_object_name = 'assignments'
    roles = ['SUPER_ADMIN']
    paginate_by = 10

    def get_queryset(self):
        qs = FacultySubjectAssignment.objects.select_related('faculty', 'subject', 'department', 'semester__course', 'academic_year').all()
        dept = self.request.GET.get('department', '')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs.order_by('academic_year__academic_year', 'faculty__full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context


class FacultyAssignmentCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = FacultySubjectAssignment
    form_class = FacultySubjectAssignmentForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('faculty_assignment_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Faculty Subject Assignment recorded.")
        return super().form_valid(form)


class FacultyAssignmentUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = FacultySubjectAssignment
    form_class = FacultySubjectAssignmentForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('faculty_assignment_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Assignment details modified.")
        return super().form_valid(form)


class FacultyAssignmentDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = FacultySubjectAssignment
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('faculty_assignment_list')
    roles = ['SUPER_ADMIN']

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q

from accounts.decorators import RoleRequiredMixin
from academics.models import Department, Semester, Section, Course, Subject
from staff.models import Staff
from notifications.models import Notification
from .models import TimetableSlot
from .forms import TimetableSlotForm

class TimetableListView(LoginRequiredMixin, View):
    def get(self, request):
        slots = TimetableSlot.objects.select_related(
            'department', 'course', 'semester', 'section', 'subject', 'faculty'
        ).all()

        # Load Dropdowns for Filters
        departments = Department.objects.all()
        semesters = Semester.objects.all()
        sections = Section.objects.all()
        faculties = Staff.objects.all()

        # Filters logic
        dept_id = request.GET.get('department')
        if dept_id:
            slots = slots.filter(department_id=dept_id)

        sem_id = request.GET.get('semester')
        if sem_id:
            slots = slots.filter(semester_id=sem_id)

        sec_id = request.GET.get('section')
        if sec_id:
            slots = slots.filter(section_id=sec_id)

        fac_id = request.GET.get('faculty')
        if fac_id:
            slots = slots.filter(faculty_id=fac_id)

        classroom_val = request.GET.get('classroom', '').strip()
        if classroom_val:
            slots = slots.filter(classroom__icontains=classroom_val)

        # Structure weekly slots grid: day -> list of slots
        days_order = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
        weekly_grid = {day: [] for day in days_order}
        
        for slot in slots:
            weekly_grid[slot.day].append(slot)

        # Sort slots within each day by start_time
        for day in days_order:
            weekly_grid[day].sort(key=lambda s: s.start_time)

        context = {
            'departments': departments,
            'semesters': semesters,
            'sections': sections,
            'faculties': faculties,
            'weekly_grid': weekly_grid,
            'query_params': request.GET,
        }
        return render(request, 'timetable/timetable_grid.html', context)


class TimetableSlotCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = TimetableSlot
    form_class = TimetableSlotForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('timetable_grid')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        response = super().form_valid(form)
        slot = self.object
        
        # Trigger automatic notifications when timetable slot is added
        # Notify faculty
        Notification.send_notification(
            user=slot.faculty.user,
            title="Timetable Slot Added",
            message=f"You have been assigned to teach '{slot.subject.name}' on {slot.get_day_display()} at {slot.start_time} in {slot.classroom}."
        )
        
        messages.success(self.request, "Timetable slot added successfully.")
        return response


class TimetableSlotUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = TimetableSlot
    form_class = TimetableSlotForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('timetable_grid')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        response = super().form_valid(form)
        slot = self.object
        
        # Notify faculty
        Notification.send_notification(
            user=slot.faculty.user,
            title="Timetable Slot Updated",
            message=f"Your lecture slot for '{slot.subject.name}' on {slot.get_day_display()} was modified. New details: {slot.start_time}-{slot.end_time} in {slot.classroom}."
        )
        
        messages.success(self.request, "Timetable slot updated successfully.")
        return response


class TimetableSlotDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = TimetableSlot
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('timetable_grid')
    roles = ['SUPER_ADMIN']

    def post(self, request, *args, **kwargs):
        slot = self.get_object()
        
        # Notify faculty before deletion
        Notification.send_notification(
            user=slot.faculty.user,
            title="Timetable Slot Cancelled",
            message=f"Your lecture slot for '{slot.subject.name}' on {slot.get_day_display()} at {slot.start_time} was cancelled."
        )
        
        messages.success(request, "Timetable slot deleted successfully.")
        return super().post(request, *args, **kwargs)

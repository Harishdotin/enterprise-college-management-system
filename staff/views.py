from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.contrib.auth import get_user_model

from accounts.decorators import RoleRequiredMixin
from .models import Staff
from .forms import StaffForm, StaffProfileForm
from academics.models import Department
import traceback 

User = get_user_model()

class StaffListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Staff
    template_name = 'staff/staff_list.html'
    context_object_name = 'staff_members'
    paginate_by = 10
    roles = ['SUPER_ADMIN', 'STAFF']

    def get_queryset(self):
        queryset = Staff.objects.select_related('department', 'user').all()
        
        # Search filter
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(employee_id__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(designation__icontains=search_query)
            )
            
        # Dropdown filters
        dept_filter = self.request.GET.get('department', '')
        if dept_filter:
            queryset = queryset.filter(department_id=dept_filter)
            
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(employment_status=status_filter)
            
        # Sorting
        sort_by = self.request.GET.get('sort', 'employee_id')
        if sort_by in ['employee_id', '-employee_id', 'full_name', '-full_name', 'date_of_joining', '-date_of_joining']:
            queryset = queryset.order_by(sort_by)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        context['query_params'] = self.request.GET.dict()
        return context


class StaffCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Staff
    form_class = StaffForm
    template_name = 'staff/staff_form.html'
    success_url = reverse_lazy('staff_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        try:
            with transaction.atomic():
                emp_id = form.cleaned_data['employee_id']
                email = form.cleaned_data['email']
                full_name = form.cleaned_data['full_name']
                phone = form.cleaned_data['phone_number']
                
                names = full_name.split(' ', 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ''
                
                # Create related User Account
                user = User.objects.create_user(
                    username=emp_id,
                    email=email,
                    password="Password@123",  # default credential
                    role='STAFF',
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone,
                    is_staff=True  # faculty can access admin parts if needed
                )
                
                # Create Staff Profile
                # Create Staff Profile
                staff = form.save(commit=False)
                staff.user = user
                staff.created_by = self.request.user
                staff.save()
                
                messages.success(
                    self.request,
                    f"Staff member {staff.full_name} registered successfully. Default login password is 'Password@123'."
                )
                
                return redirect(self.success_url)
          # <-- add this at the top of staff/views.py
        
        
        except Exception:
            traceback.print_exc()
            raise


class StaffUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Staff
    form_class = StaffForm
    template_name = 'staff/staff_form.html'
    success_url = reverse_lazy('staff_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        try:
            with transaction.atomic():
                staff = form.save()
                user = staff.user
                user.email = staff.email
                names = staff.full_name.split(' ', 1)
                user.first_name = names[0]
                user.last_name = names[1] if len(names) > 1 else ''
                user.phone_number = staff.phone_number
                user.save()
                
                messages.success(self.request, f"Staff member {staff.full_name} details updated successfully.")
                return redirect(self.get_success_url())
        except Exception as e:
            form.add_error(None, f"Error updating user account: {str(e)}")
            return self.form_invalid(form)


class StaffDetailView(LoginRequiredMixin, DetailView):
    model = Staff
    template_name = 'staff/staff_detail.html'
    context_object_name = 'staff_member'

    def dispatch(self, request, *args, **kwargs):
        staff = self.get_object()
        if request.user.role in ['SUPER_ADMIN', 'STAFF'] or request.user == staff.user:
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "Access denied. You do not have permission to view this staff profile.")
        return redirect('access_denied')


class StaffDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Staff
    template_name = 'staff/staff_confirm_delete.html'
    success_url = reverse_lazy('staff_list')
    roles = ['SUPER_ADMIN']

    def post(self, request, *args, **kwargs):
        staff = self.get_object()
        try:
            with transaction.atomic():
                staff.user.delete()  # Cascades and deletes the profile record
                messages.success(request, f"Staff member {staff.full_name} deleted successfully.")
                return redirect(self.get_success_url())
        except Exception as e:
            messages.error(request, f"Error deleting record: {str(e)}")
            return redirect('staff_list')


class StaffSelfProfileView(LoginRequiredMixin, UpdateView):
    model = Staff
    form_class = StaffProfileForm
    template_name = 'staff/profile.html'
    
    def get_object(self, queryset=None):
        return get_object_or_404(Staff, user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if request.user.role == 'STAFF':
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "Access restricted to staff accounts.")
        return redirect('access_denied')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                staff = form.save()
                user = staff.user
                user.email = staff.email
                names = staff.full_name.split(' ', 1)
                user.first_name = names[0]
                user.last_name = names[1] if len(names) > 1 else ''
                user.phone_number = staff.phone_number
                user.save()
                messages.success(self.request, "Your profile details have been updated successfully.")
                return redirect('staff_self_profile')
        except Exception as e:
            form.add_error(None, f"Error updating profile: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('staff_self_profile')

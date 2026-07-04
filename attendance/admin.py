from django.contrib import admin
from .models import StudentAttendance, StaffAttendance, LeaveRequest

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'subject', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__register_number', 'student__full_name')

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('staff__employee_id', 'staff__full_name')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('user__username',)# Register your models here.

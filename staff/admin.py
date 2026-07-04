from django.contrib import admin
from .models import Staff

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'department', 'designation', 'employment_status')
    list_filter = ('department', 'employment_status', 'date_of_joining')
    search_fields = ('employee_id', 'full_name', 'email')
    ordering = ('employee_id',)

from django.contrib import admin
from .models import Department, Course, Semester

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'duration_years')
    list_filter = ('department',)
    search_fields = ('name', 'code')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('number', 'course')
    list_filter = ('course',)

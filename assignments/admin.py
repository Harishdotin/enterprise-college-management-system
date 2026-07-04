from django.contrib import admin
from .models import Assignment, AssignmentSubmission, StudyMaterial

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'created_by', 'due_date', 'maximum_marks')
    list_filter = ('department', 'semester', 'due_date')
    search_fields = ('title', 'subject__code')

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'is_late', 'marks_obtained')
    list_filter = ('is_late', 'submitted_at')
    search_fields = ('student__register_number', 'assignment__title')

@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'uploaded_by', 'uploaded_at')
    list_filter = ('department', 'semester', 'uploaded_at')
    search_fields = ('title', 'subject__code')


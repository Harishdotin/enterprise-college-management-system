from django.contrib import admin
from .models import Student, Feedback

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('register_number', 'admission_number', 'full_name', 'department', 'course', 'semester', 'status')
    list_filter = ('department', 'course', 'semester', 'status', 'academic_year')
    search_fields = ('register_number', 'admission_number', 'full_name', 'email')
    ordering = ('register_number',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('feedback_type', 'rating', 'student', 'is_anonymous', 'created_at')
    list_filter = ('feedback_type', 'rating', 'is_anonymous', 'created_at')


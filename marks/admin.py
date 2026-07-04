from django.contrib import admin
from .models import GradeRule, Exam, StudentMark

@admin.register(GradeRule)
class GradeRuleAdmin(admin.ModelAdmin):
    list_display = ('grade_letter', 'min_score', 'max_score', 'grade_point', 'is_pass')
    ordering = ('-grade_point',)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'subject', 'exam_date', 'maximum_marks', 'status')
    list_filter = ('exam_type', 'status', 'exam_date')
    search_fields = ('name', 'subject__code')

@admin.register(StudentMark)
class StudentMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'marks_obtained', 'grade_letter', 'grade_point')
    list_filter = ('grade_letter', 'exam__exam_type')
    search_fields = ('student__register_number', 'student__full_name', 'exam__name')

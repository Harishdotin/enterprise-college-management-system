from django.db import models
from django.conf import settings
from django.utils import timezone

class Assignment(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    file = models.FileField(upload_to='assignments/', blank=True, null=True)
    department = models.ForeignKey(
        'academics.Department', 
        on_delete=models.CASCADE, 
        related_name='student_assignments'
    )
    course = models.ForeignKey(
        'academics.Course', 
        on_delete=models.CASCADE, 
        related_name='student_assignments'
    )
    semester = models.ForeignKey(
        'academics.Semester', 
        on_delete=models.CASCADE, 
        related_name='student_assignments'
    )
    subject = models.ForeignKey(
        'academics.Subject', 
        on_delete=models.CASCADE, 
        related_name='student_assignments'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_assignments'
    )
    due_date = models.DateTimeField()
    maximum_marks = models.IntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - {self.subject.code}"


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='submissions'
    )
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='assignment_submissions'
    )
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    faculty_comments = models.TextField(blank=True, null=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):
        # Auto check lateness
        now = timezone.now()
        if self.assignment and now > self.assignment.due_date:
            self.is_late = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.register_number} - {self.assignment.title} (Late: {self.is_late})"


class StudyMaterial(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='study_materials/')
    department = models.ForeignKey(
        'academics.Department', 
        on_delete=models.CASCADE, 
        related_name='study_materials'
    )
    course = models.ForeignKey(
        'academics.Course', 
        on_delete=models.CASCADE, 
        related_name='study_materials'
    )
    semester = models.ForeignKey(
        'academics.Semester', 
        on_delete=models.CASCADE, 
        related_name='study_materials'
    )
    subject = models.ForeignKey(
        'academics.Subject', 
        on_delete=models.CASCADE, 
        related_name='study_materials'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_materials'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.subject.code})"

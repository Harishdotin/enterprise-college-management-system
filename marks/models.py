from django.db import models
from django.core.exceptions import ValidationError

class GradeRule(models.Model):
    grade_letter = models.CharField(max_length=5, unique=True) # e.g. 'O', 'A+'
    min_score = models.IntegerField()  # min percentage threshold, e.g. 90
    max_score = models.IntegerField()  # max percentage threshold, e.g. 100
    grade_point = models.IntegerField() # e.g. 10, 9
    is_pass = models.BooleanField(default=True)

    class Meta:
        ordering = ['-grade_point']

    def __str__(self):
        return f"{self.grade_letter}: {self.min_score}% - {self.max_score}% (GP: {self.grade_point})"


class Exam(models.Model):
    TYPE_CHOICES = [
        ('INTERNAL', 'Internal Assessment'),
        ('MIDSEM', 'Mid Semester'),
        ('MODEL', 'Model Exam'),
        ('PRACTICAL', 'Practical Exam'),
        ('VIVA', 'Viva'),
        ('ENDSEM', 'End Semester'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
        ('RESULTS_PUBLISHED', 'Results Published'),
    ]

    name = models.CharField(max_length=150)
    exam_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='MIDSEM')
    academic_year = models.ForeignKey(
        'academics.AcademicYear', 
        on_delete=models.CASCADE, 
        related_name='exams'
    )
    department = models.ForeignKey(
        'academics.Department', 
        on_delete=models.CASCADE, 
        related_name='exams'
    )
    course = models.ForeignKey(
        'academics.Course', 
        on_delete=models.CASCADE, 
        related_name='exams'
    )
    semester = models.ForeignKey(
        'academics.Semester', 
        on_delete=models.CASCADE, 
        related_name='exams'
    )
    section = models.ForeignKey(
        'academics.Section', 
        on_delete=models.CASCADE, 
        related_name='exams',
        null=True,
        blank=True
    )
    subject = models.ForeignKey(
        'academics.Subject', 
        on_delete=models.CASCADE, 
        related_name='exams'
    )
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    maximum_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-exam_date', 'start_time']

    def __str__(self):
        return f"{self.name} - {self.subject.code} ({self.get_exam_type_display()})"


class StudentMark(models.Model):
    exam = models.ForeignKey(
        Exam, 
        on_delete=models.CASCADE, 
        related_name='marks'
    )
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='marks'
    )
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade_letter = models.CharField(max_length=5, blank=True)
    grade_point = models.IntegerField(default=0, blank=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('exam', 'student')
        ordering = ['student__register_number']

    def clean(self):
        if self.marks_obtained is not None and self.exam:
            if self.marks_obtained > self.exam.maximum_marks:
                raise ValidationError(f"Marks obtained cannot exceed maximum exam marks ({self.exam.maximum_marks}).")
            if self.marks_obtained < 0:
                raise ValidationError("Marks obtained cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Calculate grade matching rules
        max_marks = float(self.exam.maximum_marks)
        obtained = float(self.marks_obtained)
        pct = (obtained / max_marks) * 100
        
        # Query active GradeRule matching percentage
        rule = GradeRule.objects.filter(min_score__lte=pct, max_score__gte=pct).first()
        
        if rule:
            self.grade_letter = rule.grade_letter
            self.grade_point = rule.grade_point
        else:
            # Default fallback grading rules
            if obtained < float(self.exam.passing_marks):
                self.grade_letter = 'RA'  # Re-appear / Fail
                self.grade_point = 0
            elif pct >= 90:
                self.grade_letter = 'O'
                self.grade_point = 10
            elif pct >= 80:
                self.grade_letter = 'A+'
                self.grade_point = 9
            elif pct >= 70:
                self.grade_letter = 'A'
                self.grade_point = 8
            elif pct >= 60:
                self.grade_letter = 'B+'
                self.grade_point = 7
            elif pct >= 50:
                self.grade_letter = 'B'
                self.grade_point = 6
            else:
                self.grade_letter = 'RA'
                self.grade_point = 0
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.register_number} - {self.exam.subject.code}: {self.marks_obtained}/{self.exam.maximum_marks} ({self.grade_letter})"

from django.db import models
from django.core.exceptions import ValidationError

class AcademicYear(models.Model):
    academic_year = models.CharField(max_length=9, unique=True)  # e.g., '2026-2027'
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    def clean(self):
        if self.is_active:
            qs = AcademicYear.objects.filter(is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one Academic Year can be active at a time.")
                
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_active:
            # Set other years to inactive
            AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.academic_year}"


class Department(models.Model):
    STATUS_CHOICES = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    hod = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='headed_departments'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(models.Model):
    STATUS_CHOICES = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]
    code = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    duration_years = models.IntegerField(default=4)
    total_semesters = models.IntegerField(default=8)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.name} ({self.code})"


class Semester(models.Model):
    STATUS_CHOICES = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semesters')
    number = models.IntegerField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='semesters', null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')

    class Meta:
        unique_together = ('course', 'number')
        ordering = ['number']
        
    def __str__(self):
        year = self.academic_year.academic_year if self.academic_year else "No Academic Year"
        course = self.course.code if self.course else "No Course"
        return f"{course} - Semester {self.number} ({year})"


class Section(models.Model):
    name = models.CharField(max_length=5)  # e.g., 'A', 'B'
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='sections')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='sections')
    capacity = models.IntegerField(default=60)
    class_advisor = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='advised_sections'
    )

    class Meta:
        unique_together = ('semester', 'name')

    def __str__(self):
        return f"{self.semester.course.code} - Sem {self.semester.number} Section {self.name}"


class Subject(models.Model):
    STATUS_CHOICES = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]
    TYPE_CHOICES = [('THEORY', 'Theory'), ('PRACTICAL', 'Practical')]
    
    code = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    credits = models.IntegerField(default=3)
    faculty = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subjects'
    )
    subject_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='THEORY')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.name} ({self.code})"


class Class(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classes')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='classes')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='classes')
    class_advisor = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='classes'
    )

    class Meta:
        unique_together = ('semester', 'section')

    def __str__(self):
        return f"{self.course.code} Sem {self.semester.number} ({self.section.name})"


class FacultySubjectAssignment(models.Model):
    faculty = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='assignments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='assignments')

    class Meta:
        unique_together = ('faculty', 'subject', 'academic_year')

    def __str__(self):
        return f"{self.faculty.full_name} -> {self.subject.name} ({self.academic_year.academic_year})"

from django.db import models
from django.conf import settings
from academics.models import Department, Course, Semester

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='student_profile'
    )
    
    # Identification
    register_number = models.CharField(max_length=50, unique=True)
    admission_number = models.CharField(max_length=50, unique=True)
    
    # Core personal details
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    
    # Academics
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='students')
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='students')
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name='students')
    section = models.CharField(max_length=5, default='A')
    academic_year = models.CharField(max_length=9)  # e.g., '2026-2027'
    
    # Contact
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=15)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50, default='India')
    pin_code = models.CharField(max_length=10)
    
    # Media & Status
    profile_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_students'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.register_number})"


class Feedback(models.Model):
    TYPE_CHOICES = [
        ('FACULTY', 'Faculty Feedback'),
        ('SUBJECT', 'Subject Feedback'),
        ('COURSE', 'Course Feedback'),
        ('INFRASTRUCTURE', 'Infrastructure Feedback'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks'
    )
    feedback_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='FACULTY')
    faculty = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks'
    )
    subject = models.ForeignKey(
        'academics.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks'
    )
    rating = models.IntegerField(default=5)  # e.g. 1 to 5 stars
    comments = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        stud_str = "Anonymous" if self.is_anonymous else (self.student.full_name if self.student else "User")
        return f"{self.get_feedback_type_display()} from {stud_str} (Rating: {self.rating})"

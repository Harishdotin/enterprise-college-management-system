from django.db import models
from django.conf import settings

class Staff(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
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
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='staff_profile'
    )
    
    # Identification & Role
    employee_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=150)
    profile_photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    
    # Personal Info
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    
    # Professional details
    qualification = models.CharField(max_length=150)
    designation = models.CharField(max_length=100)
    department = models.ForeignKey(
        'academics.Department', 
        on_delete=models.PROTECT, 
        related_name='staff_members',
        blank=True,
        null=True
    )
    
    # Contacts
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50, default='India')
    pin_code = models.CharField(max_length=10)
    
    # Employment
    date_of_joining = models.DateField()
    employment_status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_staff_members'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"

from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models

class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        STAFF = 'STAFF', 'Staff'
        STUDENT = 'STUDENT', 'Student'
        
    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.STUDENT,
        help_text="Designates the system role for access control."
    )
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    objects = UserManager()

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN or self.is_superuser
        
    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF
        
    @property
    def is_student_member(self):
        return self.role == self.Role.STUDENT

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

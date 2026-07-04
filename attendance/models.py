from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class StudentAttendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALFDAY', 'Half Day'),
        ('LEAVE', 'Leave'),
    ]

    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    date = models.DateField()
    subject = models.ForeignKey(
        'academics.Subject', 
        on_delete=models.CASCADE, 
        related_name='attendance_records',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PRESENT')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'date', 'subject')
        ordering = ['-date', 'student__register_number']

    def __str__(self):
        sub_str = f" - {self.subject.code}" if self.subject else ""
        return f"{self.student.full_name} ({self.date}{sub_str}): {self.status}"


class StaffAttendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALFDAY', 'Half Day'),
        ('LEAVE', 'Leave'),
    ]

    staff = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PRESENT')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('staff', 'date')
        ordering = ['-date', 'staff__employee_id']

    def __str__(self):
        return f"{self.staff.full_name} ({self.date}): {self.status}"


class LeaveRequest(models.Model):
    TYPE_CHOICES = [
        ('SICK', 'Sick Leave'),
        ('CASUAL', 'Casual Leave'),
        ('MEDICAL', 'Medical Leave'),
        ('EMERGENCY', 'Emergency Leave'),
        ('ONDUTY', 'On Duty'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='SICK')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    supporting_document = models.FileField(upload_to='leave_docs/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_leaves'
    )
    admin_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("Leave end date must be on or after start date.")
            
            # Check for overlapping leave requests for the same user
            overlaps = LeaveRequest.objects.filter(
                user=self.user,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(status='REJECTED')
            
            if self.pk:
                overlaps = overlaps.exclude(pk=self.pk)
                
            if overlaps.exists():
                raise ValidationError("You have already applied for leave during this date range.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date}): {self.status}"

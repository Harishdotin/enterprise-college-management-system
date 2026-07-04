from django.db import models
from django.core.exceptions import ValidationError

class TimetableSlot(models.Model):
    DAY_CHOICES = [
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
    ]

    TYPE_CHOICES = [
        ('CLASS', 'Class Timetable'),
        ('EXAM', 'Exam Timetable'),
    ]

    timetable_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='CLASS')
    department = models.ForeignKey(
        'academics.Department', 
        on_delete=models.CASCADE, 
        related_name='timetable_slots'
    )
    course = models.ForeignKey(
        'academics.Course', 
        on_delete=models.CASCADE, 
        related_name='timetable_slots',
        null=True,
        blank=True
    )
    semester = models.ForeignKey(
        'academics.Semester', 
        on_delete=models.CASCADE, 
        related_name='timetable_slots'
    )
    section = models.ForeignKey(
        'academics.Section', 
        on_delete=models.CASCADE, 
        related_name='timetable_slots'
    )
    subject = models.ForeignKey(
        'academics.Subject', 
        on_delete=models.CASCADE, 
        related_name='timetable_slots'
    )
    faculty = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.CASCADE, 
        related_name='timetable_slots'
    )
    classroom = models.CharField(max_length=50)
    day = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day', 'start_time']

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Slot start time must be prior to end time.")
            
            # Query base for overlaps
            overlapping_slots = TimetableSlot.objects.filter(
                day=self.day,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            
            if self.pk:
                overlapping_slots = overlapping_slots.exclude(pk=self.pk)

            # Conflict 1: Faculty overlap
            faculty_conflict = overlapping_slots.filter(faculty=self.faculty)
            if faculty_conflict.exists():
                conflict = faculty_conflict.first()
                raise ValidationError(
                    f"Faculty conflict: {self.faculty.full_name} is already teaching "
                    f"'{conflict.subject.name}' to {conflict.section} at this time."
                )

            # Conflict 2: Classroom overlap
            classroom_conflict = overlapping_slots.filter(classroom=self.classroom)
            if classroom_conflict.exists():
                conflict = classroom_conflict.first()
                raise ValidationError(
                    f"Classroom conflict: Classroom '{self.classroom}' is occupied by "
                    f"{conflict.section} for '{conflict.subject.name}' at this time."
                )

            # Conflict 3: Section overlap
            section_conflict = overlapping_slots.filter(section=self.section)
            if section_conflict.exists():
                conflict = section_conflict.first()
                raise ValidationError(
                    f"Section conflict: Section {self.section} already has a slot "
                    f"'{conflict.subject.name}' scheduled at this time."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time} | {self.subject.code} ({self.classroom})"

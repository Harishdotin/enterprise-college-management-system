from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal

class FeeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Fee Categories"

    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    name = models.CharField(max_length=150)
    department = models.ForeignKey(
        'academics.Department', 
        on_delete=models.CASCADE, 
        related_name='fee_structures'
    )
    course = models.ForeignKey(
        'academics.Course', 
        on_delete=models.CASCADE, 
        related_name='fee_structures'
    )
    semester = models.ForeignKey(
        'academics.Semester', 
        on_delete=models.CASCADE, 
        related_name='fee_structures'
    )
    academic_year = models.ForeignKey(
        'academics.AcademicYear', 
        on_delete=models.CASCADE, 
        related_name='fee_structures'
    )
    category = models.ForeignKey(
        FeeCategory, 
        on_delete=models.CASCADE, 
        related_name='fee_structures'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.name} - {self.category.name} ({self.amount})"


class Scholarship(models.Model):
    name = models.CharField(max_length=150)
    percentage = models.IntegerField(default=0)  # discount percentage, e.g. 20 for 20%
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) # absolute discount if percentage is 0
    eligible_students = models.ManyToManyField(
        'students.Student', 
        related_name='scholarships',
        blank=True
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        val_str = f"{self.percentage}%" if self.percentage > 0 else f"${self.amount}"
        return f"{self.name} ({val_str})"


class StudentFee(models.Model):
    STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partial'),
        ('PAID', 'Paid'),
    ]

    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='student_fees'
    )
    fee_structure = models.ForeignKey(
        FeeStructure, 
        on_delete=models.CASCADE, 
        related_name='student_fees'
    )
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='UNPAID')
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'fee_structure')
        ordering = ['fee_structure__due_date']

    @property
    def total_due(self):
        val = self.fee_structure.amount + self.fine_amount - self.discount_amount
        return max(Decimal('0.00'), val)

    @property
    def remaining_balance(self):
        val = self.total_due - self.amount_paid
        return max(Decimal('0.00'), val)

    def clean(self):
        if self.amount_paid is not None:
            # We fetch total_due locally
            total = self.fee_structure.amount + self.fine_amount - self.discount_amount
            if self.amount_paid > total:
                raise ValidationError("Amount paid cannot exceed total due amount.")
            if self.amount_paid < 0:
                raise ValidationError("Amount paid cannot be negative.")

    def save(self, *args, **kwargs):
        # Auto-compute discount from student's scholarships
        scholarships = self.student.scholarships.filter(is_active=True)
        disc = Decimal('0.00')
        base_amount = self.fee_structure.amount
        
        for s in scholarships:
            if s.percentage > 0:
                disc += base_amount * Decimal(s.percentage) / Decimal('100.00')
            else:
                disc += s.amount
                
        # Limit discount to base amount
        self.discount_amount = min(base_amount, disc)
        
        # Calculate status
        total = base_amount + self.fine_amount - self.discount_amount
        if self.amount_paid >= total:
            self.status = 'PAID'
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        else:
            self.status = 'UNPAID'
            
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.register_number} - {self.fee_structure.name}: {self.status} (Balance: {self.remaining_balance})"


class Payment(models.Model):
    MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('UPI', 'UPI'),
        ('TRANSFER', 'Bank Transfer'),
    ]

    student_fee = models.ForeignKey(
        StudentFee, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    receipt_number = models.CharField(max_length=50, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='CASH')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"{self.receipt_number} - {self.amount_paid} ({self.payment_mode})"


class PaymentAuditLog(models.Model):
    action = models.CharField(max_length=150)
    student_fee = models.ForeignKey(
        StudentFee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    details = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.timestamp}"

import csv
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Count, Q, Avg, Sum, F, DecimalField
from decimal import Decimal
from django.contrib.auth import get_user_model

from accounts.decorators import RoleRequiredMixin
from notifications.models import Notification
from students.models import Student
from academics.models import Department, Semester, Section, Course, AcademicYear
from .models import FeeCategory, FeeStructure, Scholarship, StudentFee, Payment, PaymentAuditLog
from .forms import FeeCategoryForm, FeeStructureForm, ScholarshipForm, RecordPaymentForm, FineAdjustmentForm

User = get_user_model()

# ----------------- FINANCIAL DASHBOARD -----------------
class FinancialDashboardView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN']

    def get(self, request):
        today = datetime.date.today()
        first_of_month = today.replace(day=1)
        
        # Calculate stats
        total_collected = Payment.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        todays_collection = Payment.objects.filter(paid_at__date=today).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        monthly_collection = Payment.objects.filter(paid_at__date__gte=first_of_month).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        total_scholarships = StudentFee.objects.aggregate(total=Sum('discount_amount'))['total'] or Decimal('0.00')
        total_fines = StudentFee.objects.aggregate(total=Sum('fine_amount'))['total'] or Decimal('0.00')

        # Outstanding balances calculation
        student_fees = StudentFee.objects.all()
        total_due_bills = sum([sf.total_due for sf in student_fees])
        total_paid_bills = sum([sf.amount_paid for sf in student_fees])
        total_outstanding = total_due_bills - total_paid_bills

        # Department wise collections
        dept_collections = Payment.objects.values(
            'student_fee__student__department__code'
        ).annotate(
            total=Sum('amount_paid')
        ).order_by('-total')

        # Fee category wise collections
        category_collections = Payment.objects.values(
            'student_fee__fee_structure__category__name'
        ).annotate(
            total=Sum('amount_paid')
        ).order_by('-total')

        context = {
            'total_collected': total_collected,
            'todays_collection': todays_collection,
            'monthly_collection': monthly_collection,
            'total_scholarships': total_scholarships,
            'total_fines': total_fines,
            'total_outstanding': total_outstanding,
            'dept_collections': dept_collections,
            'category_collections': category_collections,
        }
        return render(request, 'fees/financial_dashboard.html', context)


# ----------------- FEE STRUCTURE CRUD -----------------
class FeeStructureListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = FeeStructure
    template_name = 'fees/fee_structure_list.html'
    context_object_name = 'structures'
    roles = ['SUPER_ADMIN']


class FeeStructureCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('fee_structure_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            struct = self.object
            
            # Automatically generate StudentFee records for all students matching target semester & course
            students = Student.objects.filter(
                course=struct.course,
                semester=struct.semester,
                status='ACTIVE'
            )
            
            count = 0
            for student in students:
                StudentFee.objects.get_or_create(
                    student=student,
                    fee_structure=struct
                )
                count += 1
                
                # Notify student
                Notification.send_notification(
                    user=student.user,
                    title="Fee Payment Due",
                    message=f"A new invoice for '{struct.name}' ({struct.category.name}) totaling {struct.amount} has been issued. Due date: {struct.due_date}."
                )
                
            messages.success(self.request, f"Fee structure created. Auto-billed {count} registered students.")
            return response


class FeeStructureUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('fee_structure_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        messages.success(self.request, "Fee structure details updated.")
        return super().form_valid(form)


class FeeStructureDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = FeeStructure
    template_name = 'academics/academic_confirm_delete.html'
    success_url = reverse_lazy('fee_structure_list')
    roles = ['SUPER_ADMIN']


# ----------------- STUDENT INVOICES & PAYMENTS -----------------
class StudentFeesListView(LoginRequiredMixin, View):
    def get(self, request):
        student = getattr(request.user, 'student_profile', None)
        
        # lookup for admin/staff
        lookup_reg = request.GET.get('register_number')
        if lookup_reg and request.user.role in ['SUPER_ADMIN', 'STAFF']:
            student = Student.objects.filter(register_number=lookup_reg).first()

        if not student:
            messages.error(request, "Student account configuration not found.")
            return redirect('dashboard_home')

        # Retrieve active billing invoices
        fees = StudentFee.objects.filter(student=student).select_related('fee_structure__category')
        
        # Payment History
        payments = Payment.objects.filter(student_fee__student=student).select_related('student_fee__fee_structure')

        context = {
            'student': student,
            'fees_list': fees,
            'payment_history': payments,
            'payment_form': RecordPaymentForm(),
            'fine_form': FineAdjustmentForm(),
        }
        return render(request, 'fees/student_fees.html', context)


class RecordPaymentView(LoginRequiredMixin, View):
    def post(self, request, fee_id):
        student_fee = get_object_or_404(StudentFee, pk=fee_id)
        
        # Restrict standard students from registering card/cash payments manually without authorization checks
        # For demo: simulated UPI/Card payment is allowed for students themselves!
        form = RecordPaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount_paid']
            mode = form.cleaned_data['payment_mode']
            txn_id = form.cleaned_data['transaction_id'] or f"SIM-{int(datetime.datetime.now().timestamp())}"
            remarks = form.cleaned_data['remarks']
            
            if amount > student_fee.remaining_balance:
                messages.error(request, f"Payment exceeds outstanding balance of {student_fee.remaining_balance}.")
                return redirect(f"/fees/student/invoice/?register_number={student_fee.student.register_number}")
                
            try:
                with transaction.atomic():
                    # Generate unique receipt number
                    receipt_num = f"REC-{datetime.date.today().year}-{1000 + Payment.objects.count()}"
                    
                    # Record payment
                    payment = Payment.objects.create(
                        student_fee=student_fee,
                        receipt_number=receipt_num,
                        amount_paid=amount,
                        payment_mode=mode,
                        transaction_id=txn_id,
                        remarks=remarks
                    )
                    
                    # Update billing account ledger
                    student_fee.amount_paid += amount
                    student_fee.save()
                    
                    # Log Audit entry
                    PaymentAuditLog.objects.create(
                        action="RECORD_PAYMENT",
                        student_fee=student_fee,
                        details=f"Simulated payment of {amount} registered via mode {mode}. Receipt: {receipt_num}.",
                        performed_by=request.user
                    )
                    
                    # Notifications
                    Notification.send_notification(
                        user=student_fee.student.user,
                        title="Payment Completed",
                        message=f"Payment of {amount} was received successfully. Receipt: {receipt_num}."
                    )
                    
                messages.success(request, f"Simulated payment registered successfully! Receipt: {receipt_num}.")
            except Exception as e:
                messages.error(request, f"Payment failed: {str(e)}")
        else:
            messages.error(request, "Invalid payment input parameters.")
            
        return redirect(f"/fees/student/invoice/?register_number={student_fee.student.register_number}")


# ----------------- FINE ADJUSTMENT -----------------
class FineManageView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN']

    def post(self, request, fee_id):
        student_fee = get_object_or_404(StudentFee, pk=fee_id)
        action = request.POST.get('action') # 'ADD' or 'WAIVE'
        
        form = FineAdjustmentForm(request.POST)
        if form.is_valid():
            fine_val = form.cleaned_data['fine_amount']
            remarks = form.cleaned_data['remarks']
            
            try:
                with transaction.atomic():
                    if action == 'ADD':
                        student_fee.fine_amount += fine_val
                        details_str = f"Added late fine of {fine_val}. Remarks: {remarks}."
                        notif_title = "Fine Applied"
                    else:
                        student_fee.fine_amount = max(Decimal('0.00'), student_fee.fine_amount - fine_val)
                        details_str = f"Waived fine of {fine_val}. Remarks: {remarks}."
                        notif_title = "Fine Waived"
                        
                    student_fee.save()
                    
                    # Audit Log entry
                    PaymentAuditLog.objects.create(
                        action=f"FINE_{action}",
                        student_fee=student_fee,
                        details=details_str,
                        performed_by=request.user
                    )
                    
                    # Notify student
                    Notification.send_notification(
                        user=student_fee.student.user,
                        title=notif_title,
                        message=f"Details: {details_str}. Total outstanding updated."
                    )
                messages.success(request, f"Ledger fine adjustments resolved: {action}.")
            except Exception as e:
                messages.error(request, f"Failed fine process: {str(e)}")
        else:
            messages.error(request, "Invalid fine inputs.")
            
        return redirect(f"/fees/student/invoice/?register_number={student_fee.student.register_number}")


# ----------------- RECEIPT DETAILS -----------------
class ReceiptDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'fees/receipt_detail.html'
    context_object_name = 'payment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment = self.object
        context['student_fee'] = payment.student_fee
        context['student'] = payment.student_fee.student
        context['today_date'] = datetime.datetime.now()
        return context


# ----------------- FINANCIAL REPORTS -----------------
class FinancialReportsView(LoginRequiredMixin, RoleRequiredMixin, View):
    roles = ['SUPER_ADMIN']

    def get(self, request):
        fees = StudentFee.objects.select_related('student', 'fee_structure').all()
        
        # Filters
        dept_id = request.GET.get('department')
        if dept_id:
            fees = fees.filter(student__department_id=dept_id)
            
        status = request.GET.get('status')
        if status:
            fees = fees.filter(status=status)
            
        # Export logic
        export_mode = request.GET.get('export')
        if export_mode == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Reg Number', 'Student Name', 'Fee Title', 'Bill Amount', 'Fines', 'Discounts', 'Paid Amount', 'Dues Remaining', 'Status'])
            
            for f in fees[:500]:
                writer.writerow([
                    f.student.register_number,
                    f.student.full_name,
                    f.fee_structure.name,
                    f.fee_structure.amount,
                    f.fine_amount,
                    f.discount_amount,
                    f.amount_paid,
                    f.remaining_balance,
                    f.status
                ])
            return response
            
        departments = Department.objects.all()
        context = {
            'fees_list': fees[:100],  # limit preview
            'departments': departments,
            'query_params': request.GET,
        }
        return render(request, 'fees/financial_reports.html', context)


# ----------------- SCHOLARSHIP VIEW -----------------
class ScholarshipListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Scholarship
    template_name = 'fees/scholarship_list.html'
    context_object_name = 'scholarships'
    roles = ['SUPER_ADMIN']


class ScholarshipCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Scholarship
    form_class = ScholarshipForm
    template_name = 'academics/academic_form.html'
    success_url = reverse_lazy('scholarship_list')
    roles = ['SUPER_ADMIN']

    def form_valid(self, form):
        response = super().form_valid(form)
        scholarship = self.object
        
        # Trigger notifications & recalculate active invoices
        for student in scholarship.eligible_students.all():
            Notification.send_notification(
                user=student.user,
                title="Scholarship Approved",
                message=f"You have been awarded the '{scholarship.name}' scholarship. Discount adjustment applied."
            )
            # Re-save student fees to trigger scholarship calculation override
            for sf in StudentFee.objects.filter(student=student):
                sf.save()
                
        messages.success(self.request, "Scholarship rule configured.")
        return response

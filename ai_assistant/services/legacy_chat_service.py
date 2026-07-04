import time
from decimal import Decimal
from django.db.models import Avg, Sum
from django.utils import timezone

from academics.models import Department, Course, Semester, Subject
from students.models import Student
from staff.models import Staff
from attendance.models import StudentAttendance, LeaveRequest
from marks.models import StudentMark
from fees.models import StudentFee, Payment
from assignments.models import Assignment, AssignmentSubmission
from ai_assistant.models import AIConfiguration, AIAuditLog

class ContextQueryEngine:
    @staticmethod
    def get_student_context(student):
        # Attendance context
        attendance = StudentAttendance.objects.filter(student=student)
        total_days = attendance.count()
        present_days = attendance.filter(status='PRESENT').count()
        att_pct = (present_days / total_days * 100) if total_days > 0 else 100.0

        # Exam results and GPA context
        marks = StudentMark.objects.filter(student=student).select_related('subject', 'exam')
        exam_grades = []
        for m in marks:
            exam_grades.append(f"{m.exam.name} - {m.subject.name}: {m.marks_obtained}/{m.exam.max_marks} (Grade: {m.grade_letter})")

        # Pending assignments
        now = timezone.now()
        assignments = Assignment.objects.filter(course=student.course, semester=student.semester, due_date__gte=now)
        submissions = AssignmentSubmission.objects.filter(student=student)
        submitted_ids = submissions.values_list('assignment_id', flat=True)
        pending_assign = assignments.exclude(id__in=submitted_ids)

        # Fees invoices context
        fees = StudentFee.objects.filter(student=student)
        total_due = sum(f.total_due() for f in fees)
        total_paid = sum(f.amount_paid for f in fees)
        remaining_balance = total_due - total_paid

        context = {
            'role': 'STUDENT',
            'name': student.full_name,
            'reg_num': student.register_number,
            'course': student.course.code,
            'semester': student.semester.number,
            'attendance_pct': round(att_pct, 1),
            'grades': exam_grades,
            'pending_assignments_count': pending_assign.count(),
            'outstanding_fees': float(remaining_balance)
        }
        return context

    @staticmethod
    def get_staff_context(staff):
        # Department & classes
        dept = staff.department
        students_count = Student.objects.filter(department=dept).count()
        leaves_to_review = LeaveRequest.objects.filter(status='PENDING').count()

        context = {
            'role': 'STAFF',
            'name': staff.full_name,
            'department': dept.code,
            'department_students': students_count,
            'pending_leaves_review': leaves_to_review
        }
        return context

    @staticmethod
    def get_admin_context():
        total_students = Student.objects.filter(status='ACTIVE').count()
        total_staff = Staff.objects.count()
        
        # Financial stats
        total_collected = Payment.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        total_billed = StudentFee.objects.all()
        outstanding = sum(f.remaining_balance() for f in total_billed)

        context = {
            'role': 'SUPER_ADMIN',
            'total_students': total_students,
            'total_staff': total_staff,
            'total_collected': float(total_collected),
            'outstanding_fees': float(outstanding)
        }
        return context


class AIServiceLayer:
    @staticmethod
    def get_response(user, user_message):
        start_time = time.time()
        config = AIConfiguration.get_config()

        # Build prompt context based on role
        context = {}
        if user.role == 'STUDENT':
            student = getattr(user, 'student_profile', None)
            if student:
                context = ContextQueryEngine.get_student_context(student)
        elif user.role == 'STAFF':
            staff = getattr(user, 'staff_profile', None)
            if staff:
                context = ContextQueryEngine.get_staff_context(staff)
        else:
            context = ContextQueryEngine.get_admin_context()

        # Run mock / rule-based AI processing fallback
        response, intent = AIServiceLayer._process_rule_based_ai(user_message, context)

        execution_time = int((time.time() - start_time) * 1000)
        
        # Log audit entry
        AIAuditLog.objects.create(
            user=user,
            query=user_message,
            intent=intent,
            execution_time_ms=execution_time,
            status='SUCCESS'
        )

        return response

    @staticmethod
    def _process_rule_based_ai(msg, ctx):
        msg = msg.lower().strip()
        role = ctx.get('role', 'STUDENT')

        if 'attendance' in msg:
            if role == 'STUDENT':
                return f"Hello! Your current class attendance is **{ctx['attendance_pct']}%**. Recommended guideline is to maintain above 75% to avoid exam rules disqualifications.", "check_attendance"
            return f"Hello Faculty member! Currently, you can check student attendance ratios from the rosters page. Student risk analysis is fully operational.", "check_attendance"

        if 'gpa' in msg or 'grade' in msg or 'marks' in msg:
            if role == 'STUDENT':
                grades_str = ", ".join(ctx['grades']) if ctx['grades'] else "No exams results recorded yet."
                return f"Hello! Your grades context is: {grades_str}. Focus on inheritance/polymorphism rules to maintain GPA trends.", "check_grades"
            return "Hello! Student grade averages and course performance indicators are loaded on the analytics panel.", "check_grades"

        if 'fee' in msg or 'invoice' in msg or 'bill' in msg:
            if role == 'STUDENT':
                return f"Hello Jane! Your outstanding semester tuition invoice balance is **${ctx['outstanding_fees']}**. Payments can be processed via UPI/Installments.", "check_fees"
            return f"Hello Admin! Total outstanding collection dues are **${ctx['outstanding_fees']}**. Reminders are recommended.", "check_fees"

        if 'assignment' in msg or 'deadline' in msg:
            if role == 'STUDENT':
                return f"Hello! You have **{ctx['pending_assignments_count']} pending assignment(s)** requiring submission upload on the portal.", "check_assignments"
            return f"Hello Staff! Check student submission uploads status inside assignments details view.", "check_assignments"

        # General greetings
        return f"Hello! I am your AI College Assistant. How can I assist you with attendance, grades, assignments, fee structures, or timetable slots today?", "general"

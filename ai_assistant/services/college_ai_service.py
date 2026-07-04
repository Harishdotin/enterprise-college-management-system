import time
import logging
from typing import Any, Dict, List, Optional
from django.utils import timezone
from django.db.models import Q
from accounts.models import User
from academics.models import Department, Course, Subject
from students.models import Student
from staff.models import Staff
from attendance.models import StudentAttendance
from marks.models import StudentMark
from fees.models import StudentFee
from assignments.models import Assignment, AssignmentSubmission
from notifications.models import Notification
from timetable.models import TimetableSlot
from ai_assistant.services.ai_service import AIService

logger = logging.getLogger("ai_assistant")

class StudentContextBuilder:
    @staticmethod
    def build(student: Student) -> str:
        return (
            f"Student Profile:\n"
            f"- Name: {student.full_name}\n"
            f"- Register No: {student.register_number}\n"
            f"- Department: {student.department.name} ({student.department.code})\n"
            f"- Course: {student.course.name}\n"
            f"- Semester: Semester {student.semester.number}\n"
            f"- Section: {student.section.name}\n"
            f"- Status: {student.status}\n"
        )

class AttendanceContextBuilder:
    @staticmethod
    def build(attendance_qs) -> str:
        total = attendance_qs.count()
        if total == 0:
            return "Attendance Context: No attendance records found."
        
        present = attendance_qs.filter(status='PRESENT').count()
        absent = attendance_qs.filter(status='ABSENT').count()
        pct = round((present / total) * 100, 1)
        
        return (
            f"Attendance Context:\n"
            f"- Total Days Tracked: {total}\n"
            f"- Days Present: {present}\n"
            f"- Days Absent: {absent}\n"
            f"- Current Attendance: {pct}%\n"
            f"- Minimum Requirement: 75%\n"
            f"- Examination Eligibility: {'Eligible' if pct >= 75.0 else 'Ineligible / Shortage'}\n"
        )

class MarksContextBuilder:
    @staticmethod
    def build(marks_qs) -> str:
        if not marks_qs.exists():
            return "Academic Marks Context: No graded marks recorded for this semester."
            
        lines = ["Academic Marks & Grades Context:"]
        fail_count = 0
        total_obtained = 0
        total_max = 0
        
        for mark in marks_qs:
            lines.append(
                f"- Exam: {mark.exam.name} | Subject: {mark.subject.name} ({mark.subject.code}) | "
                f"Obtained: {mark.marks_obtained}/{mark.exam.max_marks} | Grade: {mark.grade_letter} | "
                f"Pass: {'Yes' if mark.marks_obtained >= 40 else 'No'}"
            )
            total_obtained += mark.marks_obtained
            total_max += mark.exam.max_marks
            if mark.marks_obtained < 40:
                fail_count += 1
                
        overall_pct = round((total_obtained / total_max * 100), 1) if total_max > 0 else 0
        predicted_gpa = round((overall_pct / 100) * 10, 2)
        
        lines.append(f"- Cumulative Score Percentage: {overall_pct}%")
        lines.append(f"- Estimated GPA: {predicted_gpa}")
        lines.append(f"- Weak / Failed Subjects Count: {fail_count}")
        return "\n".join(lines)

class FeesContextBuilder:
    @staticmethod
    def build(fees_qs) -> str:
        if not fees_qs.exists():
            return "Fees & Invoices Context: No fees configurations setup."
            
        lines = ["Financial Fees Context:"]
        total_due = 0
        total_paid = 0
        
        for fee in fees_qs:
            due = fee.total_due()
            paid = fee.amount_paid
            pending = due - paid
            total_due += due
            total_paid += paid
            lines.append(
                f"- Category: {fee.fee_category.name} | Total Billed: ${due} | "
                f"Paid: ${paid} | Pending Balance: ${pending} | Status: {fee.status}"
            )
            
        lines.append(f"- Total Billed Amount: ${total_due}")
        lines.append(f"- Total Amount Paid: ${total_paid}")
        lines.append(f"- Total Pending Balance: ${total_due - total_paid}")
        return "\n".join(lines)

class TimetableContextBuilder:
    @staticmethod
    def build(slots_qs) -> str:
        if not slots_qs.exists():
            return "Timetable Slot Context: No scheduled lectures found."
            
        lines = ["Lecture Timetable Context:"]
        for slot in slots_qs:
            lines.append(
                f"- Day: {slot.day} | Time: {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')} | "
                f"Subject: {slot.subject.name} ({slot.subject.code}) | Classroom: {slot.classroom} | Faculty: {slot.faculty.full_name}"
            )
        return "\n".join(lines)

class AssignmentContextBuilder:
    @staticmethod
    def build(assignments_qs, submissions_qs) -> str:
        if not assignments_qs.exists():
            return "Assignments Context: No assignments allocated."
            
        submitted_ids = submissions_qs.values_list('assignment_id', flat=True)
        pending_assignments = assignments_qs.exclude(id__in=submitted_ids)
        
        lines = ["Assignments Context:"]
        lines.append(f"- Total Allocated: {assignments_qs.count()}")
        lines.append(f"- Total Submitted: {len(submitted_ids)}")
        lines.append(f"- Pending Submissions: {pending_assignments.count()}")
        
        if pending_assignments.exists():
            lines.append("Pending List:")
            for assign in pending_assignments[:5]:
                lines.append(f"  • {assign.title} | Subject: {assign.subject.name} | Due: {assign.due_date.strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)

class NotificationContextBuilder:
    @staticmethod
    def build(notifications_qs) -> str:
        if not notifications_qs.exists():
            return "Announcements Context: No recent notifications."
            
        lines = ["Campus Notifications Context:"]
        for notice in notifications_qs[:8]:
            lines.append(
                f"- [{notice.created_at.strftime('%Y-%m-%d')}] [{notice.notification_type}] "
                f"Title: {notice.title} | Content: {notice.message[:100]}..."
            )
        return "\n".join(lines)


class CollegeAIService:
    """
    CollegeAIService parses queries to identify campus intents, resolves database security bounds, 
    compiles context using modular builders, and calls the primary AI Service.
    """

    @staticmethod
    def detect_intent(message: str) -> str:
        """
        Keyword matching intent classifier mapping queries to specific CMS models.
        """
        msg = message.lower().strip()
        
        if any(kw in msg for kw in ['attendance', 'present', 'absent', 'missed classes', 'attendance %']):
            return "ATTENDANCE"
        elif any(kw in msg for kw in ['marks', 'grade', 'score', 'gpa', 'cgpa', 'fail', 'result', 'report card']):
            return "MARKS"
        elif any(kw in msg for kw in ['fee', 'payment', 'due', 'bill', 'balance', 'invoice', 'tuition', 'scholarship']):
            return "FEES"
        elif any(kw in msg for kw in ['assignment', 'homework', 'task', 'submission', 'project help']):
            return "ASSIGNMENTS"
        elif any(kw in msg for kw in ['timetable', 'schedule', 'class today', 'lecture', 'slot', 'calendar']):
            return "TIMETABLE"
        elif any(kw in msg for kw in ['notification', 'announcement', 'notice', 'alert', 'news']):
            return "NOTIFICATIONS"
        elif any(kw in msg for kw in ['leave letter', 'leave application', 'excuse letter', 'absent application']):
            return "LEAVE_LETTER"
        elif any(kw in msg for kw in ['student', 'profile', 'about me', 'my details', 'register number']):
            return "STUDENT_INFO"
        elif any(kw in msg for kw in ['department', 'course', 'subject', 'syllabus']):
            return "COURSES"
        elif any(kw in msg for kw in ['faculty', 'teacher', 'professor', 'staff', 'instructor']):
            return "FACULTY"
        
        return "GENERAL"

    @classmethod
    def process_secure_chat(cls, user: User, user_message: str) -> Dict[str, Any]:
        """
        Execute user chat requests, applying role-based authorization constraints, 
        and caching context where applicable.
        """
        start_time = time.time()
        intent = cls.detect_intent(user_message)
        
        # Build prompt context based on detected intent and user authorization
        db_context = ""
        query_count = 0
        
        # Role-based context loader
        try:
            if user.role == 'STUDENT':
                student = Student.objects.select_related('department', 'course', 'semester', 'section').get(user=user)
                db_context, query_count = cls._get_student_db_context(student, intent)
                
            elif user.role == 'STAFF':
                staff = Staff.objects.select_related('department').get(user=user)
                db_context, query_count = cls._get_staff_db_context(staff, intent)
                
            elif user.role == 'SUPER_ADMIN':
                db_context, query_count = cls._get_admin_db_context(intent)
                
            else:
                db_context = "Role Context: Unauthorized access level."

        except Exception as e:
            db_context = f"Role Context Resolution Error: {str(e)}"

        # Enhance query prompt by compiling context
        system_instruction_addendum = (
            f"\n\n[COLLEGE DATABASE LIVE CONTEXT]\n"
            f"{db_context}\n"
            f"[END OF COLLEGE DATABASE CONTEXT]\n"
            f"You MUST use this context information to answer questions. If the user asks about attendance, marks, fees, or timetable slots, answer using these statistics precisely. Format outputs using emojis, bold texts, lists, and grids where applicable."
        )

        # Send context + question to AI Service
        ai_service = AIService()
        service_result = ai_service.process_chat_query(
            user_name=user.username,
            raw_prompt=user_message,
            system_instruction=ai_service.prompt_builder.get_system_prompt(user.role) + system_instruction_addendum
        )

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Log search auditing details (Step 11)
        logger.info(
            f"[DATABASE AWARE AI] User: {user.username} | Role: {user.role} | "
            f"Intent: {intent} | DB Queries: {query_count} | Latency: {execution_time_ms}ms | "
            f"Status: {service_result['status']}"
        )

        return service_result

    @classmethod
    def _get_student_db_context(cls, student: Student, intent: str) -> tuple:
        """
        Build secure, student-scoped database context. (Step 3: Student)
        """
        context_parts = [StudentContextBuilder.build(student)]
        query_count = 1

        if intent == "ATTENDANCE":
            att = StudentAttendance.objects.filter(student=student)
            context_parts.append(AttendanceContextBuilder.build(att))
            query_count += 2
        elif intent == "MARKS":
            marks = StudentMark.objects.filter(student=student).select_related('subject', 'exam')
            context_parts.append(MarksContextBuilder.build(marks))
            query_count += 2
        elif intent == "FEES":
            fees = StudentFee.objects.filter(student=student).select_related('fee_category')
            context_parts.append(FeesContextBuilder.build(fees))
            query_count += 2
        elif intent == "TIMETABLE":
            slots = TimetableSlot.objects.filter(
                department=student.department,
                course=student.course,
                semester=student.semester,
                section=student.section
            ).select_related('subject', 'faculty')
            context_parts.append(TimetableContextBuilder.build(slots))
            query_count += 2
        elif intent == "ASSIGNMENTS":
            assigns = Assignment.objects.filter(course=student.course, semester=student.semester).select_related('subject')
            submissions = AssignmentSubmission.objects.filter(student=student)
            context_parts.append(AssignmentContextBuilder.build(assigns, submissions))
            query_count += 3
        elif intent == "NOTIFICATIONS":
            notices = Notification.objects.filter(
                Q(course=student.course, semester=student.semester) | Q(course__isnull=True)
            ).order_by('-created_at')
            context_parts.append(NotificationContextBuilder.build(notices))
            query_count += 2
        elif intent == "LEAVE_LETTER":
            context_parts.append("Prompt Instruction: Generate a leave letter application based on student details.")
        elif intent == "COURSES":
            context_parts.append(f"Course Roster: {student.course.name} ({student.course.code})")

        return "\n".join(context_parts), query_count

    @classmethod
    def _get_staff_db_context(cls, staff: Staff, intent: str) -> tuple:
        """
        Build secure, staff-scoped context. (Step 3: Faculty)
        """
        dept = staff.department
        context_parts = [f"Faculty Profile:\n- Name: {staff.full_name}\n- Department: {dept.name} ({dept.code})\n"]
        query_count = 1

        if intent == "ATTENDANCE":
            # Limited to students within their department
            students = Student.objects.filter(department=dept)
            att = StudentAttendance.objects.filter(student__in=students)
            context_parts.append(f"Department Attendance Stats: Total logs: {att.count()}. Faculty can review via rosters.")
            query_count += 2
        elif intent == "STUDENT_INFO":
            # Limited to department students
            students = Student.objects.filter(department=dept).select_related('course', 'semester')[:5]
            lines = ["Department Students Sample list:"]
            for s in students:
                lines.append(f"• {s.full_name} ({s.register_number}) | Sem {s.semester.number}")
            context_parts.append("\n".join(lines))
            query_count += 2
        elif intent == "TIMETABLE":
            # Slots allocated to this faculty
            slots = TimetableSlot.objects.filter(faculty=staff).select_related('subject', 'section', 'semester')
            context_parts.append(TimetableContextBuilder.build(slots))
            query_count += 2
        else:
            context_parts.append("Instructions: Serve faculty query context securely inside department limits.")

        return "\n".join(context_parts), query_count

    @classmethod
    def _get_admin_db_context(cls, intent: str) -> tuple:
        """
        Build admin context with full access privileges. (Step 3: Admin)
        """
        context_parts = ["Admin Access Scope: Super Admin Context (Full Privilege)"]
        query_count = 1

        if intent == "ATTENDANCE":
            total_students = Student.objects.filter(status='ACTIVE').count()
            context_parts.append(f"Global Attendance Metrics: Total Active Students: {total_students}")
            query_count += 2
        elif intent == "FEES":
            total_fees = StudentFee.objects.all()
            context_parts.append(f"Global Billing: Total billed items: {total_fees.count()}")
            query_count += 2
        else:
            context_parts.append("Global operational analytics and configuration scopes are active.")

        return "\n".join(context_parts), query_count

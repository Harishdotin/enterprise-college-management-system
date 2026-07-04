from django.utils import timezone
from students.models import Student
from fees.models import StudentFee
from marks.models import StudentMark
from assignments.models import Assignment, StudyMaterial
from .predictions_service import PredictiveIntelligenceService

class RecommendationEngine:
    @staticmethod
    def get_student_recommendations(student):
        recs = []
        
        # Check attendance risk
        att_risk = PredictiveIntelligenceService.analyze_attendance_risk(student)
        if att_risk['level'] in ['HIGH', 'MEDIUM']:
            recs.append({
                'title': "Improve Classroom Attendance",
                'description': f"Your attendance is currently {att_risk['pct']}%. Attend upcoming lectures to avoid exam rules disqualifications.",
                'type': 'ALERT'
            })

        # Check marks risk
        marks = StudentMark.objects.filter(student=student)
        for m in marks:
            if m.marks_obtained < 50:
                # Find study materials for this subject
                materials = StudyMaterial.objects.filter(subject=m.subject)[:2]
                mat_str = f" Suggested materials: {', '.join(mat.title for mat in materials)}" if materials.exists() else ""
                recs.append({
                    'title': f"Weak Focus: {m.subject.name}",
                    'description': f"Your score in {m.exam.name} was {m.marks_obtained}%. Focus on OOP guidelines.{mat_str}",
                    'type': 'STUDY'
                })

        # Check upcoming assignments
        now = timezone.now()
        upcoming = Assignment.objects.filter(course=student.course, semester=student.semester, due_date__gte=now).order_by('due_date')[:2]
        for assign in upcoming:
            recs.append({
                'title': f"Upcoming: {assign.title}",
                'description': f"Submit assignment before due date: {assign.due_date.strftime('%b %d, %H:%M')}.",
                'type': 'DEADLINE'
            })

        if not recs:
            recs.append({
                'title': "Maintain Current Performance",
                'description': "All credentials and tasks are matching academic guidelines. Keep it up!",
                'type': 'INFO'
            })

        return recs

    @staticmethod
    def get_staff_recommendations(staff):
        recs = []
        # Find students taught by staff with high risk
        dept = staff.department
        high_risk_students = Student.objects.filter(department=dept)
        
        count = 0
        for stud in high_risk_students:
            risk = PredictiveIntelligenceService.analyze_attendance_risk(stud)
            if risk['level'] == 'HIGH':
                count += 1
                if count <= 3:
                    recs.append({
                        'title': f"At-Risk: {stud.full_name}",
                        'description': f"Student has high attendance risk level ({risk['pct']}%). Intervention required.",
                        'type': 'ATTENTION'
                    })
        return recs

    @staticmethod
    def get_admin_recommendations():
        recs = []
        # Collection insights
        billed = StudentFee.objects.all()
        outstanding = sum(f.remaining_balance() for f in billed)
        if outstanding > 10000:
            recs.append({
                'title': "High Outstanding Balance Balance",
                'description': f"Outstanding student balances are cumulative: ${outstanding}. Initiate billing reminders.",
                'type': 'FINANCE'
            })
        return recs

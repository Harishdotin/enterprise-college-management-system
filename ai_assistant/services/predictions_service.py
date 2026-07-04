from django.db.models import Avg
from marks.models import StudentMark
from attendance.models import StudentAttendance

class PredictiveIntelligenceService:
    @staticmethod
    def predict_student_performance(student):
        # Predict Semester GPA based on current marks
        marks = StudentMark.objects.filter(student=student)
        if not marks.exists():
            return {
                'predicted_gpa': 8.0,
                'pass_probability': 95.0,
                'status': 'Insufficient historical marks; baseline projection active.',
                'confidence': 60.0
            }

        avg_marks_pct = marks.aggregate(avg=Avg('marks_obtained'))['avg'] or 0
        predicted_gpa = round((avg_marks_pct / 100) * 10, 2)
        
        # Cap GPA at 10.0 and minimum 0.0
        predicted_gpa = min(max(predicted_gpa, 0.0), 10.0)

        # Risk indicator
        fail_marks = marks.filter(marks_obtained__lt=40).count()
        pass_prob = 100.0 - (fail_marks * 15.0)
        pass_prob = min(max(pass_prob, 10.0), 100.0)

        # Performance bucket
        if predicted_gpa >= 8.5:
            profile = 'High-performing'
        elif predicted_gpa <= 5.0:
            profile = 'At-risk'
        else:
            profile = 'Average-performing'

        return {
            'predicted_gpa': predicted_gpa,
            'pass_probability': pass_prob,
            'performance_profile': profile,
            'confidence': 85.0
        }

    @staticmethod
    def analyze_attendance_risk(student):
        attendance = StudentAttendance.objects.filter(student=student)
        total_days = attendance.count()
        if total_days == 0:
            return {'level': 'LOW', 'trend': 'Stable', 'pct': 100.0, 'action': 'Maintain standard guidelines.'}

        present_days = attendance.filter(status='PRESENT').count()
        pct = (present_days / total_days) * 100.0

        if pct < 75.0:
            level = 'HIGH'
            action = 'Mandatory attendance warning; review leave documentation.'
            trend = 'Declining'
        elif pct < 80.0:
            level = 'MEDIUM'
            action = 'Counseling required; review class schedules.'
            trend = 'Fluctuating'
        else:
            level = 'LOW'
            action = 'No intervention required.'
            trend = 'Stable'

        return {
            'level': level,
            'trend': trend,
            'pct': round(pct, 1),
            'action': action
        }

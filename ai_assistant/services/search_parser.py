import re
from students.models import Student
from attendance.models import StudentAttendance
from fees.models import StudentFee
from .predictions_service import PredictiveIntelligenceService

class NaturalLanguageSearchParser:
    @staticmethod
    def parse_and_query(query_str):
        query_str = query_str.lower().strip()
        
        # 1. "attendance below 75%"
        if 'attendance below' in query_str or 'attendance less than' in query_str:
            match = re.search(r'\d+', query_str)
            limit = int(match.group()) if match else 75
            
            # Filter students by calculating attendance
            matching_students = []
            for student in Student.objects.all():
                att = StudentAttendance.objects.filter(student=student)
                total = att.count()
                if total > 0:
                    present = att.filter(status='PRESENT').count()
                    pct = (present / total) * 100
                    if pct < limit:
                        matching_students.append(student)
            return Student.objects.filter(id__in=[s.id for s in matching_students]), "Students with attendance below {}%".format(limit)

        # 2. "gpa above 8.5"
        if 'gpa above' in query_str or 'gpa greater than' in query_str:
            match = re.search(r'[\d\.]+', query_str)
            limit = float(match.group()) if match else 8.5
            
            matching_students = []
            for student in Student.objects.all():
                perf = PredictiveIntelligenceService.predict_student_performance(student)
                if perf['predicted_gpa'] > limit:
                    matching_students.append(student)
            return Student.objects.filter(id__in=[s.id for s in matching_students]), "Students with predicted GPA above {}".format(limit)

        # 3. "pending fee" or "outstanding fee"
        if 'pending fee' in query_str or 'outstanding' in query_str:
            matching_students = []
            for student in Student.objects.all():
                fees = StudentFee.objects.filter(student=student)
                tot = sum(f.remaining_balance() for f in fees)
                if tot > 0:
                    matching_students.append(student)
            return Student.objects.filter(id__in=[s.id for s in matching_students]), "Students with outstanding billing fee balances"

        return Student.objects.none(), "Unknown query parameter matcher"
